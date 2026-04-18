"""
Agent 2: 执行器智能体 (Executor Agent)

职责：
  - 接收 Agent1Output（偏好画像 + 环境上下文 + 关键词）
  - 从数据库按香调族群查询精油候选集
  - 纯规则计算前/中/后调配比（前调30-40%，中调30-40%，后调20-30%）
  - 根据环境系数调整最终浓度和用量
  - 估算配方成本
  - 调用 GLM 生成气味描述文案和选择理由
  - 返回 FinalOutput
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

# ── 配比区间常量 ────────────────────────────────────────────────
_TOP_RANGE    = (0.30, 0.40)   # 前调占总量比例
_MIDDLE_RANGE = (0.30, 0.40)   # 中调
_BASE_RANGE   = (0.20, 0.30)   # 后调

# 每个层级最多选取几种原料
_MAX_OILS_PER_NOTE = 3

# 浓度类型 → 香精占比 (%)
_CONCENTRATION_MAP = {
    "淡香水": 8.0,
    "香水":   15.0,
    "浓香水": 20.0,
    "香精":   28.0,
}

# 留香时长 → 小时数（取区间中值）
_LONGEVITY_MAP = {
    "2小时以内": 1.5,
    "2-4小时":   3.0,
    "4-6小时":   5.0,
    "6小时以上": 7.0,
}

# 扩散范围 → 距离描述
_SILLAGE_DISTANCE_MAP = {
    "贴身":   "约 10 cm 以内",
    "近距离": "约 30 cm",
    "中等扩散": "约 60-100 cm",
    "强扩散": "约 100 cm 以上",
}

# 预算等级 → 每毫升成本区间（元）
_BUDGET_COST_MAP = {
    "经济": (0.5, 2.0),
    "中档": (2.0, 8.0),
    "高档": (8.0, 25.0),
    "奢华": (25.0, 80.0),
}

# 标准调配总量（ml）
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

        Args:
            agent1_output: Agent1 输出的偏好画像 + 环境上下文 + 关键词

        Returns:
            FinalOutput：完整配方 + 描述文案 + 规格参数
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        logger.info(
            "[Agent2] 开始执行 | 香调=%s 浓度=%s 扩散=%s 场合=%s",
            profile.scent_families, profile.concentration,
            profile.sillage, env.occasion,
        )

        # Step 1：从数据库查询候选精油
        top_candidates, mid_candidates, base_candidates = self._select_oils(
            agent1_output.scent_keywords,
            profile.scent_families,
            profile.avoided_notes,
        )

        # Step 2：计算前/中/后调配比
        top_notes, mid_notes, base_notes = self._calculate_proportions(
            top_candidates, mid_candidates, base_candidates
        )

        # Step 3：计算规格参数（浓度、留香、扩散距离、成本）
        specs = self._calculate_specifications(profile, env, top_notes, mid_notes, base_notes)

        # Step 4：调用 GLM 生成描述文案和选择理由
        description, rationale = self._generate_description(
            agent1_output, top_notes, mid_notes, base_notes, specs
        )

        formula = PerfumeFormula(
            top_notes=top_notes,
            middle_notes=mid_notes,
            base_notes=base_notes,
        )

        output = FinalOutput(
            formula=formula,
            scent_description=description,
            selection_rationale=rationale,
            volume_ml=specs["volume_ml"],
            estimated_longevity_hours=specs["longevity_hours"],
            concentration_percentage=specs["concentration_pct"],
        )

        logger.info(
            "[Agent2] 执行完成 | 浓度=%.1f%% 留香=%.1fh 成本估算=%.1f元",
            specs["concentration_pct"], specs["longevity_hours"], specs["estimated_cost"],
        )
        return output

    # ── 私有方法：油脂选取 ──────────────────────────────────────

    def _select_oils(
        self,
        scent_keywords: list[str],
        scent_families: list[str],
        avoided_notes: list[str],
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        从数据库分别查询前/中/后调候选精油

        策略：
          1. 先用 scent_keywords 查询，尽量精准匹配
          2. 结果不足时用 scent_families 补充
          3. 过滤掉 avoided_notes 中的香调
        """
        def _filter_avoided(records: list[dict]) -> list[dict]:
            if not avoided_notes:
                return records
            result = []
            for r in records:
                family = str(r.get("scent_family") or r.get("香调族群") or "")
                name   = str(r.get("name") or r.get("名称") or "")
                if not any(av.lower() in family.lower() or av.lower() in name.lower()
                           for av in avoided_notes):
                    result.append(r)
            return result

        def _query_with_fallback(note_type: str) -> list[dict]:
            # 先用关键词查
            results = self.db.query_oils_by_scent_family(scent_keywords, note_type=note_type)
            if len(results) < _MAX_OILS_PER_NOTE:
                # 不够则用香调族群补
                extra = self.db.query_oils_by_scent_family(scent_families, note_type=note_type)
                seen_ids = {r.get("id") for r in results}
                for r in extra:
                    if r.get("id") not in seen_ids:
                        results.append(r)
            results = _filter_avoided(results)
            # 随机取 MAX_OILS_PER_NOTE 条，增加多样性
            random.shuffle(results)
            return results[:_MAX_OILS_PER_NOTE]

        top_candidates  = _query_with_fallback("前调")
        mid_candidates  = _query_with_fallback("中调")
        base_candidates = _query_with_fallback("后调")

        logger.debug(
            "[Agent2] 候选精油 | 前调=%d 中调=%d 后调=%d",
            len(top_candidates), len(mid_candidates), len(base_candidates),
        )
        return top_candidates, mid_candidates, base_candidates

    # ── 私有方法：配比计算 ──────────────────────────────────────

    def _calculate_proportions(
        self,
        top_candidates: list[dict],
        mid_candidates: list[dict],
        base_candidates: list[dict],
    ) -> tuple[list[FormulaNote], list[FormulaNote], list[FormulaNote]]:
        """
        将候选精油列表转换为带百分比的 FormulaNote 列表

        配比规则：
          - 各层级总占比：前调 30-40%，中调 30-40%，后调 20-30%（三者之和 = 100%）
          - 同层级内各精油按均匀分配（可扩展为按强度加权）
        """
        # 确定三个层级的总占比（随机在范围内取，保证合计=100）
        top_total    = round(random.uniform(*_TOP_RANGE), 2)
        base_total   = round(random.uniform(*_BASE_RANGE), 2)
        middle_total = round(1.0 - top_total - base_total, 2)
        middle_total = max(_MIDDLE_RANGE[0], min(_MIDDLE_RANGE[1], middle_total))

        def _split_evenly(candidates: list[dict], layer_total: float,
                          diffusion: str) -> list[FormulaNote]:
            if not candidates:
                return []
            each = round(100 * layer_total / len(candidates), 1)
            notes = []
            for oil in candidates:
                name = (oil.get("name_cn") or oil.get("名称")
                        or oil.get("name") or "未知原料")
                notes.append(FormulaNote(
                    name=name,
                    percentage=each,
                    diffusion_distance=diffusion,
                    ingredient_id=oil.get("id"),
                ))
            return notes

        top_notes  = _split_evenly(top_candidates,  top_total,    "近距离")
        mid_notes  = _split_evenly(mid_candidates,  middle_total, "中等")
        base_notes = _split_evenly(base_candidates, base_total,   "贴身")

        logger.debug(
            "[Agent2] 配比 | 前调=%.0f%% 中调=%.0f%% 后调=%.0f%%",
            top_total * 100, middle_total * 100, base_total * 100,
        )
        return top_notes, mid_notes, base_notes

    # ── 私有方法：规格计算 ──────────────────────────────────────

    def _calculate_specifications(
        self,
        profile: Any,
        env: Any,
        top_notes: list[FormulaNote],
        mid_notes: list[FormulaNote],
        base_notes: list[FormulaNote],
    ) -> dict[str, Any]:
        """
        计算香水规格参数：
          - concentration_pct：香精浓度（%），受环境系数微调
          - volume_ml：建议调配总量
          - longevity_hours：预估留香时长
          - diffusion_distance：扩散距离描述
          - estimated_cost：成本估算（元）
        """
        # 基础浓度
        base_conc = _CONCENTRATION_MAP.get(profile.concentration, 15.0)
        # 环境系数影响浓度（高温高湿降低，寒冷干燥提高）
        adj_conc  = round(base_conc * env.environmental_coefficient, 1)
        adj_conc  = max(5.0, min(35.0, adj_conc))   # 硬性上下限

        # 留香时长：基础值 × 环境系数的倒数（环境系数高 → 挥发快 → 留香短）
        base_longevity = _LONGEVITY_MAP.get(profile.longevity, 3.0)
        adj_longevity  = round(base_longevity / env.environmental_coefficient, 1)
        adj_longevity  = max(0.5, min(12.0, adj_longevity))

        # 调配总量（固定默认值，后续可扩展为用户自选）
        volume_ml = _DEFAULT_VOLUME_ML

        # 扩散距离
        diffusion_distance = _SILLAGE_DISTANCE_MAP.get(profile.sillage, "约 30 cm")

        # 成本估算：精油总用量 × 每毫升价格区间中值
        lo, hi = _BUDGET_COST_MAP.get(profile.budget_level, (2.0, 8.0))
        price_per_ml     = (lo + hi) / 2
        oil_volume_ml    = volume_ml * adj_conc / 100
        estimated_cost   = round(oil_volume_ml * price_per_ml, 1)

        return {
            "concentration_pct":  adj_conc,
            "volume_ml":          volume_ml,
            "longevity_hours":    adj_longevity,
            "diffusion_distance": diffusion_distance,
            "estimated_cost":     estimated_cost,
        }

    # ── 私有方法：GLM 生成描述 ──────────────────────────────────

    def _generate_description(
        self,
        agent1_output: Agent1Output,
        top_notes: list[FormulaNote],
        mid_notes: list[FormulaNote],
        base_notes: list[FormulaNote],
        specs: dict[str, Any],
    ) -> tuple[str, str]:
        """
        调用 GLM 生成面向用户的气味描述文案和配方选择理由

        Returns:
            (scent_description, selection_rationale)
        """
        profile = agent1_output.preference_profile
        env     = agent1_output.environmental_context

        def _note_names(notes: list[FormulaNote]) -> str:
            return "、".join(n.name for n in notes) if notes else "无"

        prompt = f"""你是一位诗意的香水文案师，同时也是专业调香顾问。

## 香水配方
- 前调（{_note_names(top_notes)}）：最先散发，持续约 15-30 分钟
- 中调（{_note_names(mid_notes)}）：香水核心，持续约 2-4 小时
- 后调（{_note_names(base_notes)}）：温柔尾韵，持续约 {specs['longevity_hours']:.0f} 小时

## 用户画像
- 场合：{env.occasion}，时段：{env.time_of_day}，季节：{env.season}
- 扩散范围：{profile.sillage}（{specs['diffusion_distance']}）
- 浓度：{profile.concentration}（香精占比 {specs['concentration_pct']:.1f}%）
- 体温状态：{profile.body_temp_influence}
- 活动状态：{profile.activity_influence}
- 天气：{env.temperature_range}，{env.humidity_range}

## 任务
请生成两段文字，以 JSON 格式返回：
1. scent_description：生动描述这款香水的气味层次和整体感受，150字以内，有画面感
2. selection_rationale：简述为何这个配方契合用户当前的生理状态、环境和场合，100字以内

只返回 JSON，格式：
{{"scent_description": "...", "selection_rationale": "..."}}"""

        try:
            resp = self.llm.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,   # 描述文案允许更有创意
                max_tokens=512,
            )
            raw = resp.choices[0].message.content.strip()
            data = self._parse_json(raw)
            description = data.get("scent_description", "一款为您专属调配的香水。")
            rationale   = data.get("selection_rationale", "根据您的偏好和当前环境精心调配。")

        except Exception as exc:
            logger.warning("[Agent2] GLM 描述生成失败：%s，使用默认文案", exc)
            description = f"以{_note_names(top_notes)}为前调，{_note_names(mid_notes)}为核心，{_note_names(base_notes)}收尾的专属香水。"
            rationale   = f"针对{env.occasion}场合，结合{env.season}季{env.temperature_range}天气精心调配。"

        return description, rationale

    # ── 工具方法 ────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """从模型返回文本中提取 JSON，兼容前后附加说明的情况"""
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
