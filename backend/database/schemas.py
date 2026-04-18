"""
数据模型定义 (Schemas)

定义贯穿整个业务流程的 Pydantic 数据模型：
  用户输入 → Agent1Output → Agent2处理 → FinalOutput

模型流向：
  UserInput
    └─→ Agent1Output (PreferenceProfile + EnvironmentalContext + 关键词)
          └─→ FinalOutput (PerfumeFormula + 描述文案)
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# 输入层
# ──────────────────────────────────────────────────────────────

class WeatherInfo(BaseModel):
    """天气信息，由天气 API 返回后传入 Agent1"""

    temperature: float = Field(description="当前温度（摄氏度）")
    humidity: int = Field(ge=0, le=100, description="相对湿度（%，0-100）")
    condition: str = Field(description="天气状况描述，如 晴天、阴天、小雨")


class UserInput(BaseModel):
    """用户的原始输入，API 层收集后传入处理流程"""

    text: str = Field(
        min_length=2,
        max_length=500,
        description="用户对香水的文字描述",
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="用户上传的参考图片，Base64 编码字符串",
    )
    body_temperature: Optional[float] = Field(
        default=None,
        ge=35.0,
        le=42.0,
        description="用户体温（摄氏度），影响香气挥发速度和浓度建议",
    )
    weather: Optional[WeatherInfo] = Field(
        default=None,
        description="当前天气信息，用于辅助香调推荐",
    )


# ──────────────────────────────────────────────────────────────
# Agent 1 输出层
# ──────────────────────────────────────────────────────────────

class PreferenceProfile(BaseModel):
    """用户偏好画像，由 Agent1 从用户输入中提取"""

    scent_families: list[str] = Field(
        description="偏好的香调族群，如 ['花香', '木质', '柑橘']",
    )
    concentration: Literal["淡香水", "香水", "浓香水", "香精"] = Field(
        description="香水浓度类型：淡香水(EDT) / 香水(EDP) / 浓香水 / 香精",
    )
    longevity: Literal["2小时以内", "2-4小时", "4-6小时", "6小时以上"] = Field(
        description="期望的留香时长",
    )
    sillage: Literal["贴身", "近距离", "中等扩散", "强扩散"] = Field(
        description="社交距离类型（香气扩散半径）：贴身 / 近距离 / 中等扩散 / 强扩散",
    )
    budget_level: Literal["经济", "中档", "高档", "奢华"] = Field(
        description="预算等级：经济 / 中档 / 高档 / 奢华",
    )
    avoided_notes: list[str] = Field(
        default=[],
        description="用户明确不喜欢或过敏的香调，如 ['麝香', '龙涎香']",
    )


class EnvironmentalContext(BaseModel):
    """环境上下文，由 Agent1 综合天气和场景信息生成"""

    temperature_range: Literal["寒冷(<10°C)", "凉爽(10-20°C)", "温暖(20-30°C)", "炎热(>30°C)"] = Field(
        description="温度区间分级",
    )
    humidity_range: Literal["干燥(<40%)", "适中(40-70%)", "潮湿(>70%)"] = Field(
        description="湿度区间分级",
    )
    occasion: Literal["日常", "职场", "约会", "社交聚会", "运动", "居家", "正式场合"] = Field(
        description="使用场景",
    )
    time_of_day: Literal["清晨", "上午", "下午", "傍晚", "夜间"] = Field(
        description="使用时段",
    )
    season: Literal["春", "夏", "秋", "冬"] = Field(
        description="当前季节",
    )


class Agent1Output(BaseModel):
    """Agent1（分析器）的完整输出，作为 Agent2 的输入"""

    preference_profile: PreferenceProfile = Field(
        description="从用户输入中提取的偏好画像",
    )
    environmental_context: EnvironmentalContext = Field(
        description="综合天气和场景生成的环境上下文",
    )
    scent_keywords: list[str] = Field(
        description="用于数据库检索的香气关键词列表，如 ['玫瑰', '雪松', '琥珀']",
    )
    analysis_summary: str = Field(
        description="Agent1 对用户需求的简短分析说明（100字以内）",
    )


# ──────────────────────────────────────────────────────────────
# Agent 2 输出层
# ──────────────────────────────────────────────────────────────

class FormulaNote(BaseModel):
    """香调结构中单个成分的信息"""

    name: str = Field(description="原料名称，如 佛手柑")
    percentage: float = Field(
        gt=0,
        le=100,
        description="在配方中的占比（%），同一层级所有成分之和应为100",
    )
    diffusion_distance: Literal["贴身", "近距离", "中等", "强扩散"] = Field(
        description="该成分的扩散半径级别",
    )
    ingredient_id: Optional[int] = Field(
        default=None,
        description="对应 ingredients.xlsx 中的原料 ID，可为空（使用自定义原料时）",
    )


class PerfumeFormula(BaseModel):
    """完整的香水配方，包含前中后三个层次"""

    top_notes: list[FormulaNote] = Field(
        description="前调成分列表，开瓶后最先散发，持续 15-30 分钟",
    )
    middle_notes: list[FormulaNote] = Field(
        description="中调成分列表，香水的核心，持续 2-4 小时",
    )
    base_notes: list[FormulaNote] = Field(
        description="后调成分列表，留香最持久，可达 6 小时以上",
    )


class FinalOutput(BaseModel):
    """Agent2（执行器）的最终输出，直接返回给前端"""

    formula: PerfumeFormula = Field(
        description="生成的香水配方",
    )
    scent_description: str = Field(
        description="面向用户的气味描述文案，生动描绘香水的整体感受（150字以内）",
    )
    selection_rationale: str = Field(
        description="选择该配方的理由，说明如何契合用户需求和环境（100字以内）",
    )
    volume_ml: float = Field(
        gt=0,
        description="建议调配的总量（毫升）",
    )
    estimated_longevity_hours: float = Field(
        gt=0,
        description="预估留香时长（小时）",
    )
    concentration_percentage: float = Field(
        gt=0,
        le=40,
        description="香精浓度百分比（%），决定香水类型：EDT≈10%, EDP≈15%, 香精≈25%",
    )
