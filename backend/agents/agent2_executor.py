"""
Agent 2: 执行器智能体 (Executor Agent)

三步流程：
  Step 1 _select_oils          按香调族群 + 扩散半径 + 成本系数 + 持久度从数据库筛选
  Step 2 _calculate_proportions 固定前40% / 中35% / 后25%，层内按油数均分
  Step 3 _generate_description  把实际精油的扩散距离/留香时长注入 prompt，调用 GLM 生成文案
"""

from __future__ import annotations

import json
import logging
import re
import random
from typing import Any

from openai import OpenAI

from config.settings import settings
from database.db_manager import DatabaseManager
from database.schemas import (
    Agent1Output,
    FinalOutput,
    FormulaNote,
    PerfumeFormula,
)

logger = logging.getLogger(__name__)

# ── 层级固定占比 ────────────────────────────────────────────────
_TOP_PCT    = 0.40   # 前调 40%
_MIDDLE_PCT = 0.35   # 中调 35%
_BASE_PCT   = 0.25   # 后调 25%

_MAX_OILS_PER_NOTE = 3

# ── sillage → 扩散半径范围 (cm) ────────────────────────────────
_SILLAGE_CM = {
    "贴身":    (0,   15),
    "近距离":  (15,  30),
    "中等扩散": (30, 100),
    "强扩散":  (100, 999),
}

# ── budget_level → 最大成本系数 ────────────────────────────────
_BUDGET_COST_COEF = {
    "经济": 1.0,
    "中档": 2.0,
    "高档": 5.0,
    "奢华": 999.0,
}

# ── longevity → 持久度小时范围（用于中调筛选）──────────────────
_LONGEVITY_HOURS = {
    "2小时以内": (0,  2),
    "2-4小时":   (2,  4),
    "4-6小时":   (4,  6),
    "6小时以上": (6, 99),
}

# ── concentration → 香精占比 (%) ───────────────────────────────
_CONCENTRATION_PCT = {
    "淡香水": 8.0,
    "香水":   15.0,
    "浓香水": 20.0,
    "香精":   28.0,
}

_DEFAULT_VOLUME_ML = 10.0

# ── 层位关键词（用 function + usage 文本匹配）──────────────────
_TOP_NOTE_KEYWORDS = ("顶香", "开香", "绿叶", "青草", "柠檬皮", "晨露")

_BASE_NOTE_KEYWORDS = (
    "基香", "底香", "定香", "定型", "打底", "尾调", "收尾", "留香",
    "麝香", "木质", "树脂", "琥珀", "广藿", "香草主体", "豆感", "焦糖",
)

# ── 香调族群 → 可能出现在 function/usage/name 的关键词 ─────────
_FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "花香":      ("花", "玫瑰", "茉莉", "栀子", "铃兰", "白花", "鸢尾", "紫罗兰", "覆盆子"),
    "木质":      ("木", "雪松", "檀香", "广藿", "愈创"),
    "柑橘":      ("柑", "橘", "柠檬", "佛手", "葡萄柚", "古龙", "柚", "香橙"),
    "东方/辛辣":  ("东方", "辛", "香料", "肉桂", "丁香", "琥珀", "树脂", "秘鲁", "安息香"),
    "海洋/清新":  ("海", "水生", "空气", "瓜", "晨露", "清新"),
    "美食调":    ("甜", "香草", "焦糖", "咖啡", "巧克力", "蜜", "糖", "奶", "豆感", "香兰"),
    "麝香":      ("麝",),
    "青草/绿叶":  ("草", "绿", "叶", "薄荷", "茶", "罗勒"),
}


def _row_text(row: dict) -> str:
    """拼接一条原料的所有可匹配文本字段（忽略 NaN）"""
    parts = []
    for key in ("function", "usage", "name_cn", "name", "description"):
        v = row.get(key)
        if v is None:
            continue
        s = str(v)
        if s and s.lower() != "nan":
            parts.append(s)
    return " ".join(parts)


class Agent2Executor:
    """
    执行器智能体
    将 Agent1 的偏好画像转化为具体的香水配方和文案
    """

    MODEL = "deepseek-chat"

    def __init__(self) -> None:
        self.db  = DatabaseManager.get_instance(settings.DATABASE_PATH)
        self.llm = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

    # ── 公开接口 ────────────────────────────────────────────────

    def execute(self, agent1_output: Agent1Output, language: str = "zh") -> FinalOutput:
        """
        主执行方法

        Step 1: 按多维度条件筛选精油
        Step 2: 计算前/中/后调配比
        Step 3: 调用 GLM 生成描述文案
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        logger.info(
            "[Agent2] 开始执行 | 香调=%s 扩散=%s 预算=%s 留香=%s 语言=%s",
            profile.scent_families, profile.sillage,
            profile.budget_level, profile.longevity, language,
        )

        # Step 1：按层位 + 家族关键词筛选精油
        top_oils, mid_oils, base_oils = self._select_oils(
            scent_families=profile.scent_families,
            avoided_notes=profile.avoided_notes,
        )

        # Step 2：计算配比
        top_notes, mid_notes, base_notes = self._calculate_proportions(
            top_oils, mid_oils, base_oils
        )

        # Step 3：计算规格参数
        specs = self._calculate_specifications(profile, env)

        # Step 4：调用 GLM 生成文案（把真实精油参数注入 prompt）
        description, rationale = self._generate_description(
            agent1_output, top_oils, mid_oils, base_oils,
            top_notes, mid_notes, base_notes, specs,
            language=language,
        )

        output = FinalOutput(
            formula=PerfumeFormula(
                top_notes=top_notes,
                middle_notes=mid_notes,
                base_notes=base_notes,
            ),
            scent_description=description,
            selection_rationale=rationale,
            volume_ml=specs["volume_ml"],
            estimated_longevity_hours=specs["longevity_hours"],
            concentration_percentage=specs["concentration_pct"],
        )

        logger.info(
            "[Agent2] 执行完成 | 浓度=%.1f%% 留香=%.1fh 成本=%.1f元",
            specs["concentration_pct"], specs["longevity_hours"], specs["estimated_cost"],
        )
        return output

    # ── Step 1：精油筛选 ────────────────────────────────────────

    def _select_oils(
        self,
        scent_families: list[str],
        avoided_notes: list[str],
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        根据真实 ingredients.xlsx schema 筛选精油：

          字段：function / usage / name_cn / intensity / in_stock

        流程：
          1. 过滤 in_stock=True
          2. 按 function/usage 文本把每条原料归类到 前/中/后调
          3. 每层用家族关键词匹配；匹配不到则回退到全层
          4. 排除 avoided_notes 中的关键词
        """
        all_oils = self.db.get_all_ingredients()
        if not all_oils:
            logger.warning("[Agent2] 原料库为空，返回空配方")
            return [], [], []

        # Step 1：可用库存
        stocked = [r for r in all_oils if self._truthy(r.get("in_stock"))]

        # Step 2：按层位分桶
        layer_pools: dict[str, list[dict]] = {"前调": [], "中调": [], "后调": []}
        for row in stocked:
            layer_pools[self._note_layer(row)].append(row)

        # Step 3/4：每层做家族匹配 + 过敏排除，不足则回退
        top_oils  = self._filter_and_pick(layer_pools["前调"], scent_families, avoided_notes)
        mid_oils  = self._filter_and_pick(layer_pools["中调"], scent_families, avoided_notes)
        base_oils = self._filter_and_pick(layer_pools["后调"], scent_families, avoided_notes)

        logger.info(
            "[Agent2] 筛选结果 | 前调=%d 中调=%d 后调=%d（层池: %d/%d/%d）",
            len(top_oils), len(mid_oils), len(base_oils),
            len(layer_pools["前调"]), len(layer_pools["中调"]), len(layer_pools["后调"]),
        )
        return top_oils, mid_oils, base_oils

    @staticmethod
    def _truthy(v: Any) -> bool:
        """处理 bool / 'True' / 1 / NaN 等多种可能"""
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("true", "1", "yes", "y", "t")

    @staticmethod
    def _note_layer(row: dict) -> str:
        """根据 function+usage 文本判断前/中/后调"""
        text = _row_text(row)
        if any(k in text for k in _TOP_NOTE_KEYWORDS):
            return "前调"
        if any(k in text for k in _BASE_NOTE_KEYWORDS):
            return "后调"
        return "中调"

    def _filter_and_pick(
        self,
        pool: list[dict],
        scent_families: list[str],
        avoided_notes: list[str],
    ) -> list[dict]:
        """
        在单层池里按家族关键词匹配 + 排除 avoided。
        家族匹配为空时回退为"层内任意"，保证不会返回空。
        """
        if not pool:
            return []

        # 组装当前用户选择对应的家族关键词
        family_kws: list[str] = []
        for fam in scent_families:
            family_kws.extend(_FAMILY_KEYWORDS.get(fam, (fam,)))

        def _not_avoided(row: dict) -> bool:
            if not avoided_notes:
                return True
            text = _row_text(row)
            return not any(av and av in text for av in avoided_notes)

        def _match_family(row: dict) -> bool:
            if not family_kws:
                return True
            text = _row_text(row)
            return any(kw in text for kw in family_kws)

        matched = [r for r in pool if _match_family(r) and _not_avoided(r)]

        # 家族匹配不到则回退：只排除 avoided
        if not matched:
            logger.debug("[Agent2] 层内家族无匹配，回退到全层")
            matched = [r for r in pool if _not_avoided(r)]

        if not matched:
            return []

        random.shuffle(matched)
        return matched[:_MAX_OILS_PER_NOTE]

    # ── Step 2：配比计算 ────────────────────────────────────────

    def _calculate_proportions(
        self,
        top_oils: list[dict],
        mid_oils: list[dict],
        base_oils: list[dict],
    ) -> tuple[list[FormulaNote], list[FormulaNote], list[FormulaNote]]:
        """
        固定层级占比：前调40% / 中调35% / 后调25%
        同层级内各精油均分
        """
        def _build_notes(oils: list[dict], layer_pct: float,
                         default_diffusion: str) -> list[FormulaNote]:
            if not oils:
                return []
            each_pct = round(layer_pct * 100 / len(oils), 1)
            notes = []
            for oil in oils:
                name = (oil.get("name_cn") or oil.get("名称")
                        or oil.get("name") or "未知原料")
                # 优先使用数据库中的扩散距离分级
                raw_diff = oil.get("diffusion_level") or oil.get("扩散等级")
                diffusion = str(raw_diff) if raw_diff else default_diffusion
                if diffusion not in ("贴身", "近距离", "中等", "强扩散"):
                    diffusion = default_diffusion
                notes.append(FormulaNote(
                    name=name,
                    percentage=each_pct,
                    diffusion_distance=diffusion,
                    ingredient_id=oil.get("id"),
                ))
            return notes

        top_notes  = _build_notes(top_oils,  _TOP_PCT,    "近距离")
        mid_notes  = _build_notes(mid_oils,  _MIDDLE_PCT, "中等")
        base_notes = _build_notes(base_oils, _BASE_PCT,   "贴身")

        logger.debug(
            "[Agent2] 配比 | 前调=%.0f%% 中调=%.0f%% 后调=%.0f%%",
            _TOP_PCT * 100, _MIDDLE_PCT * 100, _BASE_PCT * 100,
        )
        return top_notes, mid_notes, base_notes

    # ── Step 3：规格计算 ────────────────────────────────────────

    def _calculate_specifications(
        self,
        profile: Any,
        env: Any,
    ) -> dict[str, Any]:
        """计算浓度、留香、成本"""
        base_conc = _CONCENTRATION_PCT.get(profile.concentration, 15.0)
        adj_conc  = round(base_conc * env.environmental_coefficient, 1)
        adj_conc  = max(5.0, min(35.0, adj_conc))

        lon_lo, lon_hi = _LONGEVITY_HOURS.get(profile.longevity, (2, 4))
        base_longevity = (lon_lo + lon_hi) / 2
        adj_longevity  = round(base_longevity / env.environmental_coefficient, 1)
        adj_longevity  = max(0.5, min(12.0, adj_longevity))

        max_cost     = _BUDGET_COST_COEF.get(profile.budget_level, 2.0)
        oil_ml       = _DEFAULT_VOLUME_ML * adj_conc / 100
        # 成本估算：精油用量 × 成本系数上限作为单价参考
        estimated_cost = round(oil_ml * max_cost, 1)

        return {
            "concentration_pct":  adj_conc,
            "volume_ml":          _DEFAULT_VOLUME_ML,
            "longevity_hours":    adj_longevity,
            "diffusion_distance": f"{_SILLAGE_CM.get(profile.sillage, (0,30))[0]}-{_SILLAGE_CM.get(profile.sillage, (0,30))[1]} cm",
            "estimated_cost":     estimated_cost,
        }

    # ── Step 4：GLM 文案生成 ────────────────────────────────────

    def _generate_description(
        self,
        agent1_output: Agent1Output,
        top_oils: list[dict],
        mid_oils: list[dict],
        base_oils: list[dict],
        top_notes: list[FormulaNote],
        mid_notes: list[FormulaNote],
        base_notes: list[FormulaNote],
        specs: dict[str, Any],
        language: str = "zh",
    ) -> tuple[str, str]:
        """
        将真实精油参数（扩散距离/留香时长）和 selection_basis 注入 prompt，
        调用 DeepSeek 生成有画面感的文案和专业选择理由
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        def _oil_detail(notes: list[FormulaNote], oils: list[dict]) -> str:
            lines = []
            for note, oil in zip(notes, oils):
                desc_parts = []
                for key in ("function", "usage"):
                    v = oil.get(key)
                    if v is not None and str(v).lower() != "nan" and str(v).strip():
                        desc_parts.append(str(v).strip())
                desc = "（" + "；".join(desc_parts) + "）" if desc_parts else ""
                lines.append(f"  {note.name} {note.percentage}%{desc}")
            return "\n".join(lines) if lines else "  无"

        top_detail    = _oil_detail(top_notes,  top_oils)
        mid_detail    = _oil_detail(mid_notes,  mid_oils)
        base_detail   = _oil_detail(base_notes, base_oils)
        selection_basis = self._build_selection_basis(profile, env, specs)

        # 收集所有原料名，让 DeepSeek 一次性给出「原料 → 大众香调名」的映射
        all_notes = list(top_notes) + list(mid_notes) + list(base_notes)
        raw_names = [n.name for n in all_notes]
        naming_lines = "\n".join(f"- {n}" for n in raw_names) or "- 无"

        lang_instruction = (
            "You are a poetic perfume copywriter and professional fragrance consultant. "
            "You MUST respond entirely in English. All text fields in the JSON must be in English."
            if language == "en"
            else "你是一位诗意的香水文案师，同时也是专业调香顾问。"
        )

        prompt = f"""{lang_instruction}

## 已选定的香油配方

### 前调（持续约 15-30 分钟）
{top_detail}

### 中调（持续约 2-4 小时）
{mid_detail}

### 后调（持续约 {specs['longevity_hours']:.0f} 小时）
{base_detail}

## 用户需求画像

- 使用场合：{env.occasion}
- 使用时段：{env.time_of_day}
- 季节：{env.season}
- 扩散范围：{profile.sillage}（物理距离约 {specs['diffusion_distance']}）
- 香水浓度：{profile.concentration}（香精占比 {specs['concentration_pct']:.1f}%）
- 预算等级：{profile.budget_level}

## 生理与环境状态

- 体温状态：{profile.body_temp_influence}
- 活动强度：{profile.activity_influence}
- 天气环境：{env.temperature_range}，{env.humidity_range}

## 配方选择依据

{selection_basis}

## 任务

请生成以下三部分内容，以 JSON 格式返回：

1. **scent_description**（150字以内）
   - 生动描述这款香水的气味层次和整体感受
   - 要有画面感和情境感
   - 从前调到后调的演变过程
   - 使用诗意但不夸张的语言

2. **selection_rationale**（100字以内）
   - 简述为何这个配方契合用户当前的生理状态、环境和场合
   - 说明香油选择的科学依据
   - 专业但易懂

3. **common_names**（原料名 → 大众香调名的映射）
   - 把下面每个原料转换成消费者能一眼看懂的香调名（2-5 个汉字）
   - 去掉技术后缀（-酮/-醛/TE 级/高顺式 等），保留可识别的核心香调
   - 示例：佛手柑油→香柠檬；高顺式 HEDIONE→茉莉；甲位紫罗兰酮→紫罗兰；雪松精油 TE 级→雪松；乙基香兰素→香草；香豆素→零陵香；顺-3-己烯醇→青草
   - 每一个原料都必须映射，不得遗漏
   - 原料列表：
{naming_lines}

**只返回 JSON，格式：**
{{"scent_description": "...", "selection_rationale": "...", "common_names": {{"原料名1": "大众名1", "原料名2": "大众名2"}}}}"""

        try:
            resp = self.llm.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            raw  = resp.choices[0].message.content.strip()
            data = self._parse_json(raw)
            description = data.get("scent_description", "一款为您专属调配的香水。")
            rationale   = data.get("selection_rationale", "根据您的偏好和当前环境精心调配。")

            # 把原料学名替换为大众香调名（DeepSeek 返回的 common_names 映射）
            common = data.get("common_names") or {}
            if isinstance(common, dict):
                for note in all_notes:
                    display = common.get(note.name)
                    if display and isinstance(display, str) and display.strip():
                        note.name = display.strip()
        except Exception as exc:
            logger.warning("[Agent2] DeepSeek 文案生成失败：%s，使用兜底文案", exc)
            top_names  = ", ".join(n.name for n in top_notes)  or "none"
            mid_names  = ", ".join(n.name for n in mid_notes)  or "none"
            base_names = ", ".join(n.name for n in base_notes) or "none"
            if language == "en":
                description = f"A bespoke fragrance opening with {top_names}, blooming into {mid_names}, and settling into {base_names}."
                rationale   = f"Crafted for {env.occasion}, tailored to {env.season} season and {env.temperature_range} conditions."
            else:
                top_names  = "、".join(n.name for n in top_notes)  or "无"
                mid_names  = "、".join(n.name for n in mid_notes)  or "无"
                base_names = "、".join(n.name for n in base_notes) or "无"
                description = f"以{top_names}为前调，{mid_names}为核心，{base_names}收尾的专属香水。"
                rationale   = f"针对{env.occasion}场合，结合{env.season}季{env.temperature_range}天气精心调配。"

        return description, rationale

    def _build_selection_basis(
        self,
        profile: Any,
        env: Any,
        specs: dict[str, Any],
    ) -> str:
        """生成配方选择依据说明，注入 Agent2 prompt"""
        parts = []

        # 扩散范围依据
        parts.append(
            f"根据{profile.sillage}需求，选择扩散范围 {specs['diffusion_distance']} 的香油"
        )

        # 香调依据
        if profile.scent_families:
            parts.append(
                f"根据偏好香调（{'、'.join(profile.scent_families)}），"
                f"匹配同类香调族群的精油"
            )

        # 季节/天气依据
        parts.append(
            f"根据{env.season}季{env.temperature_range}天气，"
            f"{'选择清新香调以适应高温高湿' if '炎热' in env.temperature_range or '潮湿' in env.humidity_range else '选择适合当前气候的香调'}"
        )

        # 场合依据
        occasion_map = {
            "职场":   "职场场合要求扩散克制，避免强烈香调影响他人",
            "约会":   "约会场合可适度提升扩散，增加个人魅力",
            "运动":   "运动场合推荐清爽淡香，避免与汗味混合",
            "正式场合": "正式场合以低调优雅为主，扩散不超过近距离",
        }
        if env.occasion in occasion_map:
            parts.append(occasion_map[env.occasion])

        return "；".join(parts) + "。"

    # ── 工具方法 ────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """从模型返回文本中提取 JSON，兼容前后附加说明"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.error("[Agent2] JSON 解析失败：%s", text[:300])
        return {}
