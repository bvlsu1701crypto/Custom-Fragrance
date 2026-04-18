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

from zhipuai import ZhipuAI

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


class Agent2Executor:
    """
    执行器智能体
    将 Agent1 的偏好画像转化为具体的香水配方和文案
    """

    MODEL = "GLM-5.1"

    def __init__(self) -> None:
        self.db  = DatabaseManager.get_instance(settings.DATABASE_PATH)
        self.llm = ZhipuAI(api_key=settings.ZHIPU_API_KEY)

    # ── 公开接口 ────────────────────────────────────────────────

    def execute(self, agent1_output: Agent1Output) -> FinalOutput:
        """
        主执行方法

        Step 1: 按多维度条件筛选精油
        Step 2: 计算前/中/后调配比
        Step 3: 调用 GLM 生成描述文案
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        logger.info(
            "[Agent2] 开始执行 | 香调=%s 扩散=%s 预算=%s 留香=%s",
            profile.scent_families, profile.sillage,
            profile.budget_level, profile.longevity,
        )

        # Step 1：多维度筛选精油
        top_oils, mid_oils, base_oils = self._select_oils(
            scent_families=profile.scent_families,
            avoided_notes=profile.avoided_notes,
            sillage=profile.sillage,
            budget_level=profile.budget_level,
            longevity=profile.longevity,
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
        sillage: str,
        budget_level: str,
        longevity: str,
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        按四个维度过滤精油：
          1. 香调族群匹配（scent_families）
          2. 扩散半径在 sillage 对应的 cm 范围内
          3. 成本系数 <= budget_level 对应上限
          4. 中调持久度在 longevity 对应的小时范围内（仅对中调生效）
        """
        # 全量原料
        all_oils = self.db.get_all_ingredients()
        if not all_oils:
            logger.warning("[Agent2] 原料库为空，返回空配方")
            return [], [], []

        cm_lo,  cm_hi  = _SILLAGE_CM.get(sillage, (0, 999))
        max_cost       = _BUDGET_COST_COEF.get(budget_level, 2.0)
        lon_lo, lon_hi = _LONGEVITY_HOURS.get(longevity, (0, 99))

        def _val(row: dict, *keys, default=None):
            """按优先级取第一个有值的字段"""
            for k in keys:
                v = row.get(k)
                if v is not None:
                    return v
            return default

        def _match_family(row: dict) -> bool:
            family = str(_val(row, "scent_family", "香调族群", "scent_type", default=""))
            return any(f.lower() in family.lower() for f in scent_families)

        def _not_avoided(row: dict) -> bool:
            if not avoided_notes:
                return True
            family = str(_val(row, "scent_family", "香调族群", default=""))
            name   = str(_val(row, "name", "名称", default=""))
            return not any(av.lower() in family.lower() or av.lower() in name.lower()
                           for av in avoided_notes)

        def _in_diffusion(row: dict) -> bool:
            raw = _val(row, "diffusion_cm", "扩散半径", "diffusion_distance")
            if raw is None:
                return True   # 无数据时不过滤
            try:
                return cm_lo <= float(raw) <= cm_hi
            except (ValueError, TypeError):
                return True

        def _under_cost(row: dict) -> bool:
            raw = _val(row, "cost_coefficient", "成本系数")
            if raw is None:
                return True
            try:
                return float(raw) <= max_cost
            except (ValueError, TypeError):
                return True

        def _longevity_ok(row: dict) -> bool:
            """仅对中调生效：持久度在目标范围内"""
            raw = _val(row, "longevity_hours", "持久度", "middle_longevity_hours")
            if raw is None:
                return True
            try:
                return lon_lo <= float(raw) <= lon_hi
            except (ValueError, TypeError):
                return True

        def _note_type(row: dict) -> str:
            return str(_val(row, "note_type", "调性", "category", default=""))

        # 基础过滤：香调 + 排除 + 扩散 + 成本
        base_pool = [r for r in all_oils
                     if _match_family(r) and _not_avoided(r)
                     and _in_diffusion(r) and _under_cost(r)]

        # 按调性分桶
        top_pool  = [r for r in base_pool if "前调" in _note_type(r)]
        # 中调额外过滤持久度
        mid_pool  = [r for r in base_pool if "中调" in _note_type(r) and _longevity_ok(r)]
        base_pool_ = [r for r in base_pool if "后调" in _note_type(r)]

        def _pick(pool: list[dict], n: int) -> list[dict]:
            if not pool:
                return []
            random.shuffle(pool)
            return pool[:n]

        top_oils  = _pick(top_pool,   _MAX_OILS_PER_NOTE)
        mid_oils  = _pick(mid_pool,   _MAX_OILS_PER_NOTE)
        base_oils = _pick(base_pool_, _MAX_OILS_PER_NOTE)

        logger.debug(
            "[Agent2] 筛选结果 | 前调=%d 中调=%d 后调=%d（池: %d/%d/%d）",
            len(top_oils), len(mid_oils), len(base_oils),
            len(top_pool), len(mid_pool), len(base_pool_),
        )
        return top_oils, mid_oils, base_oils

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
    ) -> tuple[str, str]:
        """
        将真实精油参数（扩散距离/留香时长）和 selection_basis 注入 prompt，
        调用 GLM 生成有画面感的文案和专业选择理由
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        def _oil_detail(notes: list[FormulaNote], oils: list[dict]) -> str:
            lines = []
            for note, oil in zip(notes, oils):
                diff_cm  = oil.get("diffusion_cm")   or oil.get("扩散半径")   or "—"
                lon_h    = oil.get("longevity_hours") or oil.get("持久度")    or "—"
                lines.append(
                    f"  {note.name} {note.percentage}%"
                    f"（扩散半径 {diff_cm} cm，留香 {lon_h} h）"
                )
            return "\n".join(lines) if lines else "  无"

        top_detail    = _oil_detail(top_notes,  top_oils)
        mid_detail    = _oil_detail(mid_notes,  mid_oils)
        base_detail   = _oil_detail(base_notes, base_oils)
        selection_basis = self._build_selection_basis(profile, env, specs)

        prompt = f"""你是一位诗意的香水文案师，同时也是专业调香顾问。

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

请生成两段文字，以 JSON 格式返回：

1. **scent_description**（150字以内）
   - 生动描述这款香水的气味层次和整体感受
   - 要有画面感和情境感
   - 从前调到后调的演变过程
   - 使用诗意但不夸张的语言

2. **selection_rationale**（100字以内）
   - 简述为何这个配方契合用户当前的生理状态、环境和场合
   - 说明香油选择的科学依据
   - 专业但易懂

**只返回 JSON，格式：**
{{"scent_description": "...", "selection_rationale": "..."}}"""

        try:
            resp = self.llm.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512,
            )
            raw  = resp.choices[0].message.content.strip()
            data = self._parse_json(raw)
            description = data.get("scent_description", "一款为您专属调配的香水。")
            rationale   = data.get("selection_rationale", "根据您的偏好和当前环境精心调配。")
        except Exception as exc:
            logger.warning("[Agent2] GLM 文案生成失败：%s，使用兜底文案", exc)
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
