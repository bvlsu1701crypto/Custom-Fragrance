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

    MODEL = "GLM-5.1"  # 智谱 AI 模型名称

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
        q  = inp.questionnaire
        w  = inp.weather
        wd = inp.watch_data

        avoided_str    = "、".join(q.avoided_notes) if q.avoided_notes else "无"
        scent_pref_str = "、".join(q.scent_preference)
        user_text      = inp.user_text or "（无）"
        heart_rate_str = f"{wd.heart_rate} bpm" if wd.heart_rate else "未检测"

        return f"""你是一位专业的香水配方顾问，擅长根据用户的描述、生理状态、环境条件和问卷回答，推理出最适合的香水需求参数。

## 用户输入

### 用户自由描述（可能为空）
{user_text}

### 问卷回答
- 使用场合：{q.occasion}
- 偏好香调：{scent_pref_str}
- 留香时长：{q.longevity}
- 扩散范围：{q.sillage}
- 浓度偏好：{q.concentration}
- 预算等级：{q.budget_level}
- 排斥香调：{avoided_str}
- 使用时段：{q.time_of_day}

### Apple Watch 生理数据
- 体温：{wd.body_temperature}°C
- 心率：{heart_rate_str}
- 活动强度：{wd.activity_level}

### 当前环境（GPS 定位天气）
- 城市：{w.city}
- 气温：{w.temperature}°C
- 湿度：{w.humidity}%
- 天气状况：{w.condition}
- 季节：{w.season}

## 分析规则

1. **体温影响**
   - 体温 > 37°C：降低浓度建议，推荐清爽香调
   - 体温正常：按问卷偏好处理

2. **活动强度影响**
   - 剧烈运动：推荐淡香水，扩散范围降低到"贴身"或"近距离"
   - 静息/轻度活动：按问卷偏好处理

3. **环境影响**
   - 高温高湿（>28°C, >70%）：推荐清爽香调（柑橘调、水生调、草本调）
   - 寒冷干燥（<15°C, <40%）：推荐温暖香调（木质调、东方调、辛辣调）
   - 适中环境：按问卷偏好处理

4. **场合影响**
   - 职场/正式场合：扩散范围不超过"近距离"，避免甜腻香调
   - 约会/社交：扩散可达"中等扩散"
   - 运动/休闲：推荐"贴身"或"近距离"

5. **用户自由描述优先级最高**
   - 如果用户描述中明确提到需求（如"清新"、"不要太浓"、"持久一点"），应优先满足
   - 用户描述与问卷冲突时，以用户描述为准

## 输出要求

请综合以上所有信息，输出标准化的需求参数。

**严格以如下 JSON 格式返回，不要包含任何其他文字：**

{{
  "occasion": "职场 | 约会 | 运动 | 日常 | 社交 | 正式",
  "scent_preference": ["香调1", "香调2"],
  "longevity": "2小时以内 | 2-4小时 | 4-6小时 | 6小时以上",
  "sillage": "贴身 | 近距离 | 中等扩散 | 强扩散",
  "concentration": "淡香水 | 香水 | 浓香水 | 香精",
  "budget_level": "经济 | 中档 | 高档 | 奢华",
  "avoided_notes": ["排斥的香调"],
  "time_of_day": "早晨 | 上午 | 下午 | 晚间 | 全天",
  "body_temperature": {wd.body_temperature},
  "heart_rate": {wd.heart_rate if wd.heart_rate else "null"},
  "activity_level": "静息 | 轻度活动 | 中度活动 | 剧烈运动",
  "temperature": {w.temperature},
  "humidity": {w.humidity},
  "condition": "晴天 | 阴天 | 雨天",
  "season": "春 | 夏 | 秋 | 冬",
  "city": "城市名",
  "analysis_summary": "简述推理逻辑，100字以内"
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
        """
        将 LLM 返回的扁平 JSON + 生理偏移 组装为 Agent1Output

        新 prompt 返回的字段：occasion / scent_preference / longevity /
        sillage / concentration / budget_level / avoided_notes /
        time_of_day / body_temperature / heart_rate / activity_level /
        temperature / humidity / condition / season / city / analysis_summary
        """
        q = inp.questionnaire
        w = inp.weather

        # ── 从 LLM 结果读取，回退到问卷原始值 ──────────────────
        occasion     = llm_data.get("occasion",     q.occasion)
        scent_pref   = llm_data.get("scent_preference", list(q.scent_preference))
        longevity    = llm_data.get("longevity",    q.longevity)
        budget_level = llm_data.get("budget_level", q.budget_level)
        avoided      = llm_data.get("avoided_notes", q.avoided_notes)
        time_of_day  = llm_data.get("time_of_day",  q.time_of_day)
        season       = llm_data.get("season",        w.season)
        city         = llm_data.get("city",          w.city)

        # ── sillage：LLM 结果 + 生理偏移 ───────────────────────
        raw_sillage      = llm_data.get("sillage", q.sillage)
        adjusted_sillage = self._adjust_sillage(raw_sillage, sillage_offset)

        # ── concentration 规范化 ────────────────────────────────
        raw_conc      = llm_data.get("concentration", _CONCENTRATION_MAP.get(q.concentration, "香水"))
        concentration = _CONCENTRATION_MAP.get(raw_conc, raw_conc)
        if concentration not in ("淡香水", "香水", "浓香水", "香精"):
            concentration = "香水"

        # ── 环境数据优先用 LLM 精炼结果，否则回退天气原始值 ───
        temperature = float(llm_data.get("temperature", w.temperature))
        humidity    = int(llm_data.get("humidity",    w.humidity))

        preference = PreferenceProfile(
            scent_families      = scent_pref,
            concentration       = concentration,
            longevity           = longevity,
            sillage             = adjusted_sillage,
            budget_level        = budget_level,
            avoided_notes       = avoided,
            body_temp_influence = f"体温 {inp.watch_data.body_temperature}°C：{temp_note}",
            activity_influence  = f"活动强度「{inp.watch_data.activity_level}」：{activity_note}",
        )

        environment = EnvironmentalContext(
            temperature_range         = self._temp_level(temperature),
            humidity_range            = self._humidity_level(humidity),
            occasion                  = occasion,
            time_of_day               = time_of_day,
            season                    = season,
            environmental_coefficient = self._calc_env_coefficient(temperature, humidity, occasion),
        )

        # scent_keywords：用 scent_preference 作为关键词（新 prompt 不再单独输出）
        scent_keywords = scent_pref

        output = Agent1Output(
            preference_profile    = preference,
            environmental_context = environment,
            scent_keywords        = scent_keywords,
            analysis_summary      = llm_data.get("analysis_summary", "分析完成"),
        )

        logger.info(
            "[Agent1] 分析完成 | 香调=%s 浓度=%s 扩散=%s city=%s",
            preference.scent_families,
            preference.concentration,
            preference.sillage,
            city,
        )
        return output

    # ── 工具方法 ────────────────────────────────────────────────

    @staticmethod
    def _temp_level(temperature: float) -> str:
        if temperature < 10:   return "寒冷(<10°C)"
        if temperature < 20:   return "凉爽(10-20°C)"
        if temperature < 30:   return "温暖(20-30°C)"
        return "炎热(>30°C)"

    @staticmethod
    def _humidity_level(humidity: int) -> str:
        if humidity < 40:  return "干燥(<40%)"
        if humidity < 70:  return "适中(40-70%)"
        return "潮湿(>70%)"

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
