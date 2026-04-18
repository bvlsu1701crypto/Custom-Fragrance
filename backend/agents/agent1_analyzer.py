"""
Agent 1: 分析器智能体 (Analyzer Agent)

职责：
  - 接收 Agent1Input（Apple Watch 生理数据 + 问卷回答 + 天气）
  - 构建详细 prompt，调用智谱 AI GLM-5.1
  - 综合生理状态、环境条件、用户偏好，分析出最终偏好画像
  - 返回 Agent1Output（PreferenceProfile + EnvironmentalContext + 关键词）
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from zhipuai import ZhipuAI

from config.settings import settings
from database.schemas import (
    Agent1Input,
    Agent1Output,
    EnvironmentalContext,
    PreferenceProfile,
)

logger = logging.getLogger(__name__)

# ── 体温影响规则 ────────────────────────────────────────────────
# 体温越高，香气挥发越快，建议降低浓度和扩散强度
_TEMP_RULES = {
    (35.0, 36.3): ("体温偏低，香气挥发较慢，可适当提高浓度",       1),   # sillage +1级
    (36.3, 37.0): ("体温正常，无需调整",                            0),
    (37.0, 37.5): ("体温偏高，香气挥发加快，建议降低扩散强度",      -1),  # sillage -1级
    (37.5, 42.0): ("体温明显偏高，挥发速度快，建议清淡香调并减量",  -2),
}

# ── 活动强度影响规则 ────────────────────────────────────────────
_ACTIVITY_RULES = {
    "静息":    ("静息状态，扩散范围保持问卷选择",          0),
    "轻度活动": ("轻度活动，建议适当降低扩散范围",         -1),
    "中度活动": ("中度活动，体温上升，建议降低浓度和扩散",  -1),
    "剧烈运动": ("剧烈运动，出汗加速挥发，建议清爽淡香",   -2),
}

# sillage 等级列表，用于 +/- 偏移
_SILLAGE_LEVELS = ["贴身", "近距离", "中等扩散", "强扩散"]

# concentration 映射：问卷选项 → PreferenceProfile 枚举
_CONCENTRATION_MAP = {
    "淡香水(EDT)": "淡香水",
    "香水(EDP)":   "香水",
    "浓香水":      "浓香水",
    "香精":        "香精",
}


class Agent1Analyzer:
    """
    分析器智能体
    综合问卷答案和 Apple Watch 生理数据，通过 GLM-5.1 生成偏好画像
    """

    MODEL = "glm-4-flash"  # 智谱 AI 模型名称

    def __init__(self) -> None:
        self.client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)

    # ── 公开接口 ────────────────────────────────────────────────

    def analyze(self, agent_input: Agent1Input) -> Agent1Output:
        """
        主分析方法

        Args:
            agent_input: 包含 watch_data、questionnaire、weather 的完整输入

        Returns:
            Agent1Output：偏好画像 + 环境上下文 + 关键词 + 摘要
        """
        logger.info(
            "[Agent1] 开始分析 | 场合=%s 体温=%.1f°C 天气=%s %.1f°C",
            agent_input.questionnaire.occasion,
            agent_input.watch_data.body_temperature,
            agent_input.weather.condition,
            agent_input.weather.temperature,
        )

        # Step 1：计算生理影响（体温 + 活动强度），得到 sillage 偏移量
        temp_note, temp_offset    = self._calc_temp_influence(agent_input.watch_data.body_temperature)
        activity_note, act_offset = _ACTIVITY_RULES[agent_input.watch_data.activity_level]
        sillage_offset = temp_offset + act_offset

        # Step 2：调用 GLM-5.1 进行语义分析
        prompt   = self._build_prompt(agent_input, temp_note, activity_note)
        raw_json = self._call_llm(prompt)

        # Step 3：解析模型返回，构建 Agent1Output
        return self._build_output(agent_input, raw_json, sillage_offset, temp_note, activity_note)

    # ── Prompt 构建 ─────────────────────────────────────────────

    def _build_prompt(
        self,
        inp: Agent1Input,
        temp_note: str,
        activity_note: str,
    ) -> str:
        q = inp.questionnaire
        w = inp.weather
        wd = inp.watch_data

        avoided_str = "、".join(q.avoided_notes) if q.avoided_notes else "无"
        scent_pref_str = "、".join(q.scent_preference)

        return f"""你是一位专业的香水配方顾问，擅长根据用户的生理状态、环境条件和个人偏好，推荐最适合的香水方案。

## 用户问卷回答
- Q1 使用场合：{q.occasion}
- Q2 偏好香调：{scent_pref_str}
- Q3 留香时长：{q.longevity}
- Q4 扩散范围：{q.sillage}
- Q5 浓度偏好：{q.concentration}
- Q6 预算等级：{q.budget_level}
- Q7 排斥香调：{avoided_str}
- Q8 使用时段：{q.time_of_day}

## Apple Watch 生理数据
- 体温：{wd.body_temperature}°C（{temp_note}）
- 心率：{wd.heart_rate if wd.heart_rate else "未检测"} bpm
- 活动强度：{wd.activity_level}（{activity_note}）

## 当前环境（GPS 定位天气）
- 城市：{w.city}
- 气温：{w.temperature}°C（{w.temp_level}）
- 湿度：{w.humidity}%（{w.humidity_level}）
- 天气状况：{w.condition}
- 季节：{w.season}

## 分析任务
请综合以上所有信息，输出一份香水需求分析报告。注意：
1. 体温偏高（>37°C）或剧烈运动时，应降低推荐的香调浓度和扩散强度
2. 高温高湿环境下，偏向清爽香调（柑橘、海洋、青草）
3. 寒冷干燥环境下，偏向温暖香调（木质、东方、辛辣）
4. 职场/正式场合，扩散强度不宜超过"近距离"
5. 提取的关键词应为具体香料名称（如玫瑰、雪松、佛手柑），而非抽象描述

请严格以如下 JSON 格式返回，不要包含任何其他文字：
{{
  "scent_families": ["香调1", "香调2"],
  "concentration": "淡香水 | 香水 | 浓香水 | 香精",
  "longevity": "2小时以内 | 2-4小时 | 4-6小时 | 6小时以上",
  "sillage": "贴身 | 近距离 | 中等扩散 | 强扩散",
  "budget_level": "经济 | 中档 | 高档 | 奢华",
  "avoided_notes": [],
  "scent_keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "analysis_summary": "100字以内的分析说明"
}}"""

    # ── LLM 调用 ────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> dict[str, Any]:
        """
        调用智谱 AI GLM-5.1，返回解析后的 JSON dict
        若解析失败则抛出异常，由上层处理
        """
        logger.debug("[Agent1] 发送 prompt，长度=%d 字符", len(prompt))

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,   # 偏低温度，保证输出格式稳定
            max_tokens=1024,
        )

        raw_text = response.choices[0].message.content.strip()
        logger.debug("[Agent1] 模型原始返回：%s", raw_text[:200])

        return self._parse_json(raw_text)

    # ── 输出构建 ────────────────────────────────────────────────

    def _build_output(
        self,
        inp: Agent1Input,
        llm_data: dict[str, Any],
        sillage_offset: int,
        temp_note: str,
        activity_note: str,
    ) -> Agent1Output:
        """将 LLM 返回的 dict + 生理偏移 组装为 Agent1Output"""
        q = inp.questionnaire
        w = inp.weather

        # 对 sillage 应用生理偏移
        base_sillage    = llm_data.get("sillage", q.sillage)
        adjusted_sillage = self._adjust_sillage(base_sillage, sillage_offset)

        # concentration 做规范化（兼容模型可能返回的带括号格式）
        raw_conc = llm_data.get("concentration", _CONCENTRATION_MAP.get(q.concentration, "香水"))
        concentration = _CONCENTRATION_MAP.get(raw_conc, raw_conc)
        if concentration not in ("淡香水", "香水", "浓香水", "香精"):
            concentration = "香水"

        preference = PreferenceProfile(
            scent_families   = llm_data.get("scent_families", list(q.scent_preference)),
            concentration    = concentration,
            longevity        = llm_data.get("longevity", q.longevity),
            sillage          = adjusted_sillage,
            budget_level     = llm_data.get("budget_level", q.budget_level),
            avoided_notes    = llm_data.get("avoided_notes", q.avoided_notes),
            body_temp_influence = f"体温 {inp.watch_data.body_temperature}°C：{temp_note}",
            activity_influence  = f"活动强度「{inp.watch_data.activity_level}」：{activity_note}",
        )

        environment = EnvironmentalContext(
            temperature_range      = w.temp_level,
            humidity_range         = w.humidity_level,
            occasion               = q.occasion,
            time_of_day            = q.time_of_day,
            season                 = w.season,
            environmental_coefficient = self._calc_env_coefficient(w.temperature, w.humidity, q.occasion),
        )

        output = Agent1Output(
            preference_profile   = preference,
            environmental_context = environment,
            scent_keywords       = llm_data.get("scent_keywords", list(q.scent_preference)),
            analysis_summary     = llm_data.get("analysis_summary", "分析完成"),
        )

        logger.info(
            "[Agent1] 分析完成 | 香调=%s 浓度=%s 扩散=%s 关键词=%s",
            preference.scent_families,
            preference.concentration,
            preference.sillage,
            output.scent_keywords,
        )
        return output

    # ── 工具方法 ────────────────────────────────────────────────

    @staticmethod
    def _calc_temp_influence(body_temp: float) -> tuple[str, int]:
        """返回 (体温影响说明, sillage偏移量)"""
        for (lo, hi), (note, offset) in _TEMP_RULES.items():
            if lo <= body_temp < hi:
                return note, offset
        return "体温正常，无需调整", 0

    @staticmethod
    def _adjust_sillage(base: str, offset: int) -> str:
        """在 _SILLAGE_LEVELS 上做有界偏移"""
        if base not in _SILLAGE_LEVELS:
            base = "近距离"
        idx = _SILLAGE_LEVELS.index(base) + offset
        idx = max(0, min(len(_SILLAGE_LEVELS) - 1, idx))
        return _SILLAGE_LEVELS[idx]

    @staticmethod
    def _calc_env_coefficient(temperature: float, humidity: int, occasion: str) -> float:
        """计算环境系数（0.5~1.5），高温高湿/封闭场合降低用量"""
        temp_coef = (
            0.7 if temperature >= 30 else
            0.9 if temperature >= 20 else
            1.1 if temperature >= 10 else 1.3
        )
        hum_coef = (
            0.85 if humidity >= 70 else
            1.0  if humidity >= 40 else 1.15
        )
        occ_coef = {
            "日常": 1.0, "职场": 0.8, "约会": 1.1,
            "社交聚会": 1.2, "运动": 0.7, "居家": 0.9, "正式场合": 0.85,
        }.get(occasion, 1.0)

        coef = round(temp_coef * hum_coef * occ_coef, 3)
        return max(0.5, min(1.5, coef))

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """
        从模型返回文本中提取 JSON。
        兼容模型在 JSON 前后附加说明文字的情况。
        """
        # 优先尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 提取第一个 {...} 块
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.error("[Agent1] JSON 解析失败，原始返回：%s", text[:500])
        raise ValueError(f"GLM 返回内容无法解析为 JSON：{text[:200]}")
