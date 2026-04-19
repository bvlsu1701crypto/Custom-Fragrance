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
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from config.settings import settings
from database.db_manager import DatabaseManager
from database.schemas import (
    Agent1Output,
    FinalOutput,
    FormulaNote,
    PerfumeFormula,
    SimilarPerfume,
)

logger = logging.getLogger(__name__)

# ── 层级占比：由 concentration 动态决定 ─────────────────────────
# concentration → (top, middle, base)
_LAYER_RATIOS: dict[str, tuple[float, float, float]] = {
    "淡香水": (0.50, 0.30, 0.20),   # EDT：前调突出、快进快出
    "香水":   (0.40, 0.35, 0.25),   # EDP：均衡
    "浓香水": (0.35, 0.35, 0.30),   # 中后稳重
    "香精":   (0.30, 0.30, 0.40),   # Extrait：后调厚重
}
_DEFAULT_LAYER_RATIOS = (0.40, 0.35, 0.25)

# ── 层内原料权重：priority × intensity ─────────────────────────
_PRIORITY_WEIGHT = {"A": 1.2, "B": 1.0, "C": 0.8}
_INTENSITY_WEIGHT = {
    "高影响": 1.4,
    "高":     1.3,
    "中高":   1.15,
    "中":     1.0,
    "功能料": 1.0,
}

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
_TOP_NOTE_KEYWORDS = (
    # 原有：顶调/开场性词
    "顶香", "开香", "绿叶", "青草", "柠檬皮", "晨露",
    # 柑橘顶调
    "柑", "橘", "古龙", "清新顶香", "佛手",
    # 水生/海洋顶调
    "水感", "海洋水感", "海风", "瓜感", "臭氧", "空气感",
    # 芳香草本顶调
    "罗勒", "薄荷", "薰衣草",
)

# 定香/功能性辅料——单独归桶，不进三层展示
_FIXATIVE_KEYWORDS = ("定香", "溶解树脂", "溶解剂")

_BASE_NOTE_KEYWORDS = (
    # 层位显式标记
    "基香", "底香", "打底", "尾调", "收尾", "留香", "定型",
    # 典型后调原料/家族（保留真正只出现在底调的词，剔除"木质/麝香/琥珀/焦糖"等会误伤中调的家族词）
    "树脂", "广藿", "香草主体", "豆感", "安息香",
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


def _expand_avoided(avoided: list[str]) -> set[str]:
    """把用户填的族群名展开成具体关键词；非族群名保留原文兜底自由文本。"""
    expanded: set[str] = set()
    for av in avoided:
        if not av:
            continue
        if av in _FAMILY_KEYWORDS:
            expanded.update(_FAMILY_KEYWORDS[av])
        else:
            expanded.add(av)
    return expanded


def _oil_weight(oil: dict) -> float:
    """按 priority × intensity 计算原料的相对权重；未知值按 1.0。"""
    p_raw = oil.get("priority")
    i_raw = oil.get("intensity")
    p = _PRIORITY_WEIGHT.get(str(p_raw) if p_raw else "", 1.0)
    i = _INTENSITY_WEIGHT.get(str(i_raw) if i_raw else "", 1.0)
    return p * i


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

        # Step 1：按层位 + 家族关键词筛选精油
        top_oils, mid_oils, base_oils = self._select_oils(
            scent_families=profile.scent_families,
            avoided_notes=profile.avoided_notes,
        )

        # Step 2：计算配比（层比由 concentration 驱动，层内按权重分配）
        top_notes, mid_notes, base_notes = self._calculate_proportions(
            top_oils, mid_oils, base_oils, profile.concentration,
        )

        # Step 3：计算规格参数
        specs = self._calculate_specifications(profile, env)

        # Step 4：调用 GLM 生成文案（把真实精油参数注入 prompt）
        desc_zh, rationale_zh, desc_en, rationale_en, similar_perfumes = self._generate_description(
            agent1_output, top_oils, mid_oils, base_oils,
            top_notes, mid_notes, base_notes, specs,
        )

        output = FinalOutput(
            formula=PerfumeFormula(
                top_notes=top_notes,
                middle_notes=mid_notes,
                base_notes=base_notes,
            ),
            scent_description=desc_zh,
            selection_rationale=rationale_zh,
            scent_description_en=desc_en or None,
            selection_rationale_en=rationale_en or None,
            volume_ml=specs["volume_ml"],
            estimated_longevity_hours=specs["longevity_hours"],
            concentration_percentage=specs["concentration_pct"],
            similar_perfumes=similar_perfumes,
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

        # Step 2：按层位分桶（定香单独成桶，不参与前/中/后调展示）
        layer_pools: dict[str, list[dict]] = {"前调": [], "中调": [], "后调": [], "定香": []}
        for row in stocked:
            layer_pools[self._note_layer(row)].append(row)

        # Step 3/4：每层做家族匹配 + 过敏排除，不足则回退
        top_oils  = self._filter_and_pick(layer_pools["前调"], scent_families, avoided_notes)
        mid_oils  = self._filter_and_pick(layer_pools["中调"], scent_families, avoided_notes)
        base_oils = self._filter_and_pick(layer_pools["后调"], scent_families, avoided_notes)

        # 前调空兜底：从 mid_pool / stocked 里挑高挥发性原料补上
        if not top_oils:
            logger.warning("[Agent2] 前调候选被 avoid 全部排除，启动跨层兜底")
            avoided_kws = _expand_avoided(avoided_notes)
            promoted = self._promote_to_top(layer_pools["中调"], stocked, avoided_kws)
            if promoted:
                top_oils = promoted
                promoted_ids = {id(o) for o in promoted}
                mid_oils = [m for m in mid_oils if id(m) not in promoted_ids]

        logger.info(
            "[Agent2] 筛选结果 | 前调=%d 中调=%d 后调=%d（层池: %d/%d/%d，定香池=%d已隐藏）",
            len(top_oils), len(mid_oils), len(base_oils),
            len(layer_pools["前调"]), len(layer_pools["中调"]), len(layer_pools["后调"]),
            len(layer_pools["定香"]),
        )
        return top_oils, mid_oils, base_oils

    @staticmethod
    def _promote_to_top(
        mid_pool: list[dict],
        stocked: list[dict],
        avoided_kws: set[str],
    ) -> list[dict]:
        """
        前调池被 avoid 清空时的兜底：
          1. 先在 mid_pool 里挑 intensity ∈ {高影响, 高} 的高挥发原料（非 avoided），最多 2 条
          2. 不足则从 stocked 里挑 intensity 最高且非 avoided 的再补 1 条
          3. 实在不行（rare）→ 返回空，让配方真前调缺失并由上层 log
        """
        def _not_avoided(row: dict) -> bool:
            if not avoided_kws:
                return True
            text = _row_text(row)
            return not any(kw in text for kw in avoided_kws)

        high_volatile = {"高影响", "高"}

        # 1) 从中调池挑挥发性高的
        picked: list[dict] = [
            r for r in mid_pool
            if str(r.get("intensity") or "") in high_volatile and _not_avoided(r)
        ]
        random.shuffle(picked)
        picked = picked[:2]

        if picked:
            return picked

        # 2) 全库回退：挑一条 intensity 最高的非 avoided 原料
        intensity_rank = {"高影响": 3, "高": 2, "中高": 1, "中": 0, "功能料": -1}
        candidates = [r for r in stocked if _not_avoided(r)]
        candidates.sort(
            key=lambda r: intensity_rank.get(str(r.get("intensity") or ""), -1),
            reverse=True,
        )
        return candidates[:1]

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
        """
        根据 function 字段（结构角色）判断层位：
          - 定香/溶解等功能性辅料 → '定香'（不进三层展示）
          - 前调关键词 → '前调'
          - 后调关键词 → '后调'
          - 其他默认 → '中调'
        注意：只看 function，不看 usage/description，避免"usage 里出现'空气感'"
        这类气味描述把中/后调原料误判到前调。
        """
        func = str(row.get("function") or "")
        if func.lower() in ("", "nan"):
            return "中调"
        if any(k in func for k in _FIXATIVE_KEYWORDS):
            return "定香"
        if any(k in func for k in _TOP_NOTE_KEYWORDS):
            return "前调"
        if any(k in func for k in _BASE_NOTE_KEYWORDS):
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

        # 把同时出现在偏好和排斥里的家族剔除掉，防止 include/exclude 互相抵消
        avoided_set = set(avoided_notes or [])
        safe_families = [f for f in scent_families if f not in avoided_set]

        # 组装当前用户选择对应的家族关键词
        family_kws: list[str] = []
        for fam in safe_families:
            family_kws.extend(_FAMILY_KEYWORDS.get(fam, (fam,)))

        # 把 avoided 展开成具体关键词（与 include 展开对称）
        avoided_kws = _expand_avoided(avoided_notes)

        def _not_avoided(row: dict) -> bool:
            if not avoided_kws:
                return True
            text = _row_text(row)
            return not any(kw in text for kw in avoided_kws)

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
        concentration: str,
    ) -> tuple[list[FormulaNote], list[FormulaNote], list[FormulaNote]]:
        """
        层间占比：由 concentration 决定（EDT→前调重、香精→后调重）
        层内占比：按 priority × intensity 权重加权后，分配该层的整瓶占比。
        每条 FormulaNote.percentage 是 **整瓶** 百分比；同一层加和 ≈ 层占比。
        """
        def _build_notes(
            oils: list[dict],
            layer_ratio: float,
            default_diffusion: str,
        ) -> list[FormulaNote]:
            if not oils:
                return []
            weights = [_oil_weight(o) for o in oils]
            total_w = sum(weights) or 1.0
            notes = []
            for oil, w in zip(oils, weights):
                name = (oil.get("name_cn") or oil.get("名称")
                        or oil.get("name") or "未知原料")
                raw_diff = oil.get("diffusion_level") or oil.get("扩散等级")
                diffusion = str(raw_diff) if raw_diff else default_diffusion
                if diffusion not in ("贴身", "近距离", "中等", "强扩散"):
                    diffusion = default_diffusion
                each_pct = round(layer_ratio * 100 * w / total_w, 1)
                notes.append(FormulaNote(
                    name=name,
                    percentage=each_pct,
                    diffusion_distance=diffusion,
                    ingredient_id=oil.get("id"),
                ))
            return notes

        top_r, mid_r, base_r = _LAYER_RATIOS.get(concentration, _DEFAULT_LAYER_RATIOS)

        top_notes  = _build_notes(top_oils,  top_r,  "近距离")
        mid_notes  = _build_notes(mid_oils,  mid_r,  "中等")
        base_notes = _build_notes(base_oils, base_r, "贴身")

        logger.info(
            "[Agent2] 动态配比 | concentration=%s 层比=(%.0f/%.0f/%.0f) 前调=%d条 中调=%d条 后调=%d条",
            concentration, top_r * 100, mid_r * 100, base_r * 100,
            len(top_notes), len(mid_notes), len(base_notes),
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
    ) -> tuple[str, str, str, str, list[SimilarPerfume]]:
        """
        并行调用中英文 prompt，返回 (desc_zh, rationale_zh, desc_en, rationale_en, similar_perfumes)。
        英文 prompt 失败不影响中文结果。
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        all_notes = list(top_notes) + list(mid_notes) + list(base_notes)
        all_oils  = list(top_oils) + list(mid_oils) + list(base_oils)

        with ThreadPoolExecutor(max_workers=2) as pool:
            zh_future = pool.submit(
                self._call_zh_prompt,
                profile, env, top_oils, mid_oils, base_oils,
                top_notes, mid_notes, base_notes, all_notes, specs,
            )
            en_future = pool.submit(
                self._call_en_prompt,
                profile, env, top_oils, mid_oils, base_oils,
                top_notes, mid_notes, base_notes, all_notes, specs,
            )
            desc_zh, rationale_zh, common_zh, perfumes_zh = zh_future.result()
            desc_en, rationale_en, common_en, perfumes_en = en_future.result()

        # 中文 common_names 覆写 note.name（保持原有行为）
        if isinstance(common_zh, dict):
            for note in all_notes:
                display = common_zh.get(note.name)
                if display and isinstance(display, str) and display.strip():
                    note.name = display.strip()

        # 英文 common_names 写入 note.name_en
        # en prompt keys are English raw names (oil["name"]), but LLM may normalize case
        if isinstance(common_en, dict):
            common_en_lower = {k.lower().strip(): v for k, v in common_en.items()}
            for note, oil in zip(all_notes, all_oils):
                en_raw = (oil.get("name") or "").strip()
                en_name = (common_en.get(en_raw)
                           or common_en_lower.get(en_raw.lower())
                           or common_en.get(note.name))
                if en_name and isinstance(en_name, str) and en_name.strip():
                    note.name_en = en_name.strip()
                elif en_raw:
                    note.name_en = en_raw

        # 合并中英文 similar_perfumes
        # 注意：zh 字段保留 zh 文本（即使为空），en 字段保留 en 文本
        # 不要用一种语言的内容去填充另一种语言的字段，避免污染
        similar: list[SimilarPerfume] = []
        max_len = max(len(perfumes_zh), len(perfumes_en))
        for i in range(max_len):
            zh = perfumes_zh[i] if i < len(perfumes_zh) and isinstance(perfumes_zh[i], dict) else {}
            en = perfumes_en[i] if i < len(perfumes_en) and isinstance(perfumes_en[i], dict) else {}
            name_zh = str(zh.get("name", "")).strip()
            brand_zh = str(zh.get("brand", "")).strip()
            reason_zh = str(zh.get("reason", "")).strip()
            name_en = str(en.get("name", "")).strip()
            brand_en = str(en.get("brand", "")).strip()
            reason_en = str(en.get("reason", "")).strip()
            # 跳过两边都没有名字的项
            if not (name_zh or name_en):
                continue
            similar.append(SimilarPerfume(
                name=name_zh,
                name_en=name_en or None,
                brand=brand_zh,
                brand_en=brand_en or None,
                reason=reason_zh,
                reason_en=reason_en or None,
            ))

        return desc_zh, rationale_zh, desc_en, rationale_en, similar

    def _call_zh_prompt(
        self,
        profile: Any, env: Any,
        top_oils: list[dict], mid_oils: list[dict], base_oils: list[dict],
        top_notes: list[FormulaNote], mid_notes: list[FormulaNote],
        base_notes: list[FormulaNote],
        all_notes: list[FormulaNote],
        specs: dict[str, Any],
    ) -> tuple[str, str, dict, list]:
        """中文 prompt — 原有逻辑不变"""
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

        raw_names = [n.name for n in all_notes]
        naming_lines = "\n".join(f"- {n}" for n in raw_names) or "- 无"

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

请生成以下四部分内容，以 JSON 格式返回：

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

4. **similar_perfumes**（2-3 款）
   - 推荐市面上风格最接近的真实商业香水
   - 每款包含：name（香水名）、brand（品牌）、reason（50字以内说明与本配方的相似之处）
   - 必须是真实存在的商业香水，不要编造

**只返回 JSON，格式：**
{{"scent_description": "...", "selection_rationale": "...", "common_names": {{"原料名1": "大众名1"}}, "similar_perfumes": [{{"name": "...", "brand": "...", "reason": "..."}}]}}"""

        try:
            resp = self.llm.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            raw  = resp.choices[0].message.content.strip()
            data = self._parse_json(raw)
            description = data.get("scent_description", "一款为您专属调配的香水。")
            rationale   = data.get("selection_rationale", "根据您的偏好和当前环境精心调配。")
            common      = data.get("common_names") or {}
            perfumes    = data.get("similar_perfumes") or []
            if not isinstance(perfumes, list):
                perfumes = []
        except Exception as exc:
            logger.warning(
                "[Agent2] DeepSeek 中文文案生成失败：%s | raw=%s",
                exc, (locals().get("raw") or "")[:500],
                exc_info=True,
            )
            top_names  = "、".join(n.name for n in top_notes)  or "无"
            mid_names  = "、".join(n.name for n in mid_notes)  or "无"
            base_names = "、".join(n.name for n in base_notes) or "无"
            description = f"以{top_names}为前调，{mid_names}为核心，{base_names}收尾的专属香水。"
            rationale   = f"针对{env.occasion}场合，结合{env.season}季{env.temperature_range}天气精心调配。"
            common = {}
            perfumes = []

        return description, rationale, common, perfumes

    # ── 中文→英文字段映射（用于英文 prompt 输入） ─────────────────
    _EN_OCCASION: dict[str, str] = {
        "职场": "Work/Office", "约会": "Date Night", "运动": "Sports",
        "日常": "Daily Casual", "社交聚会": "Social Events",
        "正式场合": "Formal/Special", "居家": "Home",
    }
    _EN_TIME: dict[str, str] = {
        "清晨": "Early Morning", "上午": "Morning", "下午": "Afternoon",
        "傍晚": "Dusk", "夜间": "Evening",
    }
    _EN_SEASON: dict[str, str] = {
        "春": "Spring", "夏": "Summer", "秋": "Autumn", "冬": "Winter",
    }
    _EN_SILLAGE: dict[str, str] = {
        "贴身": "Intimate", "近距离": "Close Range",
        "中等扩散": "Moderate", "强扩散": "Strong Projection",
    }
    _EN_CONC: dict[str, str] = {
        "淡香水": "Eau de Toilette", "香水": "Eau de Parfum",
        "浓香水": "Parfum", "香精": "Extrait",
    }

    def _call_en_prompt(
        self,
        profile: Any, env: Any,
        top_oils: list[dict], mid_oils: list[dict], base_oils: list[dict],
        top_notes: list[FormulaNote], mid_notes: list[FormulaNote],
        base_notes: list[FormulaNote],
        all_notes: list[FormulaNote],
        specs: dict[str, Any],
    ) -> tuple[str, str, dict, list]:
        """English prompt — parallel to _call_zh_prompt"""
        def _oil_detail_en(notes: list[FormulaNote], oils: list[dict]) -> str:
            lines = []
            for note, oil in zip(notes, oils):
                en_name = oil.get("name") or note.name
                desc_parts = []
                for key in ("function", "usage"):
                    v = oil.get(key)
                    if v is not None and str(v).lower() != "nan" and str(v).strip():
                        desc_parts.append(str(v).strip())
                desc = f" ({'; '.join(desc_parts)})" if desc_parts else ""
                lines.append(f"  {en_name} {note.percentage}%{desc}")
            return "\n".join(lines) if lines else "  None"

        top_detail  = _oil_detail_en(top_notes,  top_oils)
        mid_detail  = _oil_detail_en(mid_notes,  mid_oils)
        base_detail = _oil_detail_en(base_notes, base_oils)

        occasion = self._EN_OCCASION.get(env.occasion, env.occasion)
        time_of_day = self._EN_TIME.get(env.time_of_day, env.time_of_day)
        season = self._EN_SEASON.get(env.season, env.season)
        sillage = self._EN_SILLAGE.get(profile.sillage, profile.sillage)
        concentration = self._EN_CONC.get(profile.concentration, profile.concentration)

        raw_names = [oil.get("name") or n.name for n, oil in
                     zip(all_notes, list(top_oils) + list(mid_oils) + list(base_oils))]
        naming_lines = "\n".join(f"- {n}" for n in raw_names) or "- None"

        prompt = f"""You are a poetic perfumer and professional fragrance consultant.

## Selected Fragrance Formula

### Top Notes (lasts ~15-30 minutes)
{top_detail}

### Heart Notes (lasts ~2-4 hours)
{mid_detail}

### Base Notes (lasts ~{specs['longevity_hours']:.0f} hours)
{base_detail}

## User Profile

- Occasion: {occasion}
- Time of day: {time_of_day}
- Season: {season}
- Projection: {sillage} (approx. {specs['diffusion_distance']})
- Concentration: {concentration} ({specs['concentration_pct']:.1f}%)

## Task

Return a JSON object with exactly four fields:

1. **scent_description_en** (under 150 words)
   - Vividly describe the scent journey from top to base notes
   - Paint a sensory scene with imagery and emotion
   - Poetic but not overwrought

2. **selection_rationale_en** (under 100 words)
   - Explain why this formula suits the user's occasion, season, and physiology
   - Reference specific ingredient choices and their scientific basis
   - Professional yet accessible

3. **common_names_en** (raw ingredient name → consumer-friendly English name)
   - Map each raw ingredient below to a short (1-3 word) name a consumer would recognize
   - Drop technical suffixes (-one, -al, TE grade, High-Cis, etc.)
   - Examples: Bergamot Oil → Bergamot; High Cis HEDIONE → Jasmine; Ethyl Vanillin → Vanilla; Coumarin → Tonka Bean; Cis-3-Hexen-1-ol → Green Leaf
   - Every ingredient must be mapped
   - Ingredient list:
{naming_lines}

4. **similar_perfumes_en** (2-3 items)
   - Recommend real, commercially available fragrances with the closest scent profile to this formula
   - Each item: name (perfume name), brand, reason (under 50 words explaining the similarity)
   - Must be real, well-known commercial perfumes — do not invent names

**Return JSON only:**
{{"scent_description_en": "...", "selection_rationale_en": "...", "common_names_en": {{"Ingredient1": "Name1"}}, "similar_perfumes_en": [{{"name": "...", "brand": "...", "reason": "..."}}]}}"""

        try:
            resp = self.llm.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            raw  = resp.choices[0].message.content.strip()
            data = self._parse_json(raw)
            description = data.get("scent_description_en", "")
            rationale   = data.get("selection_rationale_en", "")
            common      = data.get("common_names_en") or {}
            perfumes    = data.get("similar_perfumes_en") or []
            if not isinstance(perfumes, list):
                perfumes = []
        except Exception as exc:
            logger.warning(
                "[Agent2] DeepSeek English copy failed: %s | raw=%s",
                exc, (locals().get("raw") or "")[:500],
                exc_info=True,
            )
            description = ""
            rationale   = ""
            common = {}
            perfumes = []

        return description, rationale, common, perfumes

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
