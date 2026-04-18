"""
数据模型定义 (Schemas)

数据流向：
  AppleWatchData ──┐
                   ├──→ Agent1Input ──→ Agent1Output ──→ FinalOutput
  QuestionnaireAnswers ─┘               (偏好画像 +          (配方 +
                                         环境上下文 +          描述文案)
                                         关键词)
"""

from __future__ import annotations

import random
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# Apple Watch 数据层
# ──────────────────────────────────────────────────────────────

class AppleWatchData(BaseModel):
    """
    Apple Watch 采集的身体与位置数据
    由设备端上传，体温暂时使用随机常量模拟
    """

    body_temperature: float = Field(
        default_factory=lambda: round(random.uniform(36.3, 37.2), 1),
        ge=35.0,
        le=42.0,
        description=(
            "用户体温（摄氏度）。"
            "体温偏高时香气挥发加快，建议减少用量或选择清淡香调；"
            "体温偏低时挥发减慢，可适当提高浓度。"
            "当前为随机常量模拟，接入真实设备后替换。"
        ),
    )
    latitude: float = Field(
        ge=-90.0,
        le=90.0,
        description="用户当前位置纬度，由 Apple Watch GPS 提供，用于联网查询天气",
    )
    longitude: float = Field(
        ge=-180.0,
        le=180.0,
        description="用户当前位置经度",
    )
    heart_rate: Optional[int] = Field(
        default=None,
        ge=30,
        le=220,
        description="当前心率（bpm），可选。心率偏高（运动/紧张状态）时建议清爽香调",
    )
    activity_level: Literal["静息", "轻度活动", "中度活动", "剧烈运动"] = Field(
        default="静息",
        description="当前活动强度，由 Apple Watch 运动传感器推断",
    )


class WeatherInfo(BaseModel):
    """
    天气信息
    由 WeatherAPIService 根据 AppleWatchData 的经纬度联网获取
    """

    temperature: float = Field(description="当前气温（摄氏度）")
    humidity: int = Field(ge=0, le=100, description="相对湿度（%）")
    condition: str = Field(description="天气状况，如 晴天、阴天、小雨")
    city: str = Field(default="未知", description="所在城市名（反向地理编码）")
    season: Literal["春", "夏", "秋", "冬"] = Field(description="当前季节")
    temp_level: Literal["寒冷(<10°C)", "凉爽(10-20°C)", "温暖(20-30°C)", "炎热(>30°C)"] = Field(
        description="温度区间分级"
    )
    humidity_level: Literal["干燥(<40%)", "适中(40-70%)", "潮湿(>70%)"] = Field(
        description="湿度区间分级"
    )


# ──────────────────────────────────────────────────────────────
# 问卷回答层
# ──────────────────────────────────────────────────────────────

class QuestionnaireAnswers(BaseModel):
    """
    用户回答指定问题的结果
    前端以固定问卷形式收集，所有字段均为枚举选项，避免自由文字的歧义

    问卷题目对应关系：
      Q1 → occasion          你今天打算在什么场合使用香水？
      Q2 → scent_preference  你偏好哪类香调？（可多选）
      Q3 → longevity         你希望香水能持续多久？
      Q4 → sillage           你希望香气扩散到多远？
      Q5 → concentration     你偏好哪种香水浓度类型？
      Q6 → budget_level      你的预算大概在哪个范围？
      Q7 → avoided_notes     有没有你不喜欢或过敏的香调？（可多选，可跳过）
      Q8 → time_of_day       你计划在什么时段使用？
    """

    occasion: Literal["日常", "职场", "约会", "社交聚会", "运动", "居家", "正式场合"] = Field(
        description="Q1：使用场合"
    )
    scent_preference: list[Literal[
        "花香", "木质", "柑橘", "东方/辛辣", "海洋/清新", "美食调", "麝香", "青草/绿叶"
    ]] = Field(
        min_length=1,
        description="Q2：偏好香调族群（至少选一项，可多选）",
    )
    longevity: Literal["2小时以内", "2-4小时", "4-6小时", "6小时以上"] = Field(
        description="Q3：期望留香时长"
    )
    sillage: Literal["贴身", "近距离", "中等扩散", "强扩散"] = Field(
        description="Q4：期望香气扩散范围"
    )
    concentration: Literal["淡香水(EDT)", "香水(EDP)", "浓香水", "香精"] = Field(
        description="Q5：偏好的香水浓度类型"
    )
    budget_level: Literal["经济", "中档", "高档", "奢华"] = Field(
        description="Q6：预算等级"
    )
    avoided_notes: list[str] = Field(
        default=[],
        description="Q7：不喜欢或过敏的香调（可为空）",
    )
    time_of_day: Literal["清晨", "上午", "下午", "傍晚", "夜间"] = Field(
        description="Q8：计划使用时段"
    )


# ──────────────────────────────────────────────────────────────
# Agent 1 输入层
# ──────────────────────────────────────────────────────────────

class Agent1Input(BaseModel):
    """
    Agent1 的完整输入
    整合 Apple Watch 生理/位置数据 + 问卷回答 + 天气（由系统根据位置自动获取）
    """

    user_text: Optional[str] = Field(
        default="",
        description="用户自由输入的文字描述，优先级最高，可为空",
    )
    language: Literal["zh", "en"] = Field(
        default="zh",
        description="输出语言：zh=中文，en=英文",
    )
    watch_data: AppleWatchData = Field(
        description="Apple Watch 采集的体温、位置、心率、活动强度"
    )
    questionnaire: QuestionnaireAnswers = Field(
        description="用户对 8 个指定问题的回答"
    )
    weather: WeatherInfo = Field(
        description="由系统根据 watch_data 经纬度联网获取的当前天气"
    )


# ──────────────────────────────────────────────────────────────
# Agent 1 输出层
# ──────────────────────────────────────────────────────────────

class PreferenceProfile(BaseModel):
    """用户偏好画像，由 Agent1 综合问卷 + 生理数据分析得出"""

    scent_families: list[str] = Field(
        description="最终推荐的香调族群（Agent1 可在问卷基础上结合体温/场合微调）"
    )
    concentration: Literal["淡香水", "香水", "浓香水", "香精"] = Field(
        description="推荐浓度（综合问卷偏好 + 体温 + 活动强度）"
    )
    longevity: Literal["2小时以内", "2-4小时", "4-6小时", "6小时以上"] = Field(
        description="推荐留香时长"
    )
    sillage: Literal["贴身", "近距离", "中等扩散", "强扩散"] = Field(
        description="推荐扩散范围（体温偏高或运动状态下自动降一级）"
    )
    budget_level: Literal["经济", "中档", "高档", "奢华"] = Field(
        description="预算等级（直接来自问卷）"
    )
    avoided_notes: list[str] = Field(
        default=[],
        description="需排除的香调"
    )
    body_temp_influence: str = Field(
        description="体温对配方的影响说明，如 '体温36.8°C偏高，建议清淡前调，减少10%用量'"
    )
    activity_influence: str = Field(
        description="活动强度对配方的影响说明，如 '轻度活动状态，扩散距离保持近距离'"
    )


class EnvironmentalContext(BaseModel):
    """环境上下文，由 Agent1 综合天气信息生成"""

    temperature_range: Literal["寒冷(<10°C)", "凉爽(10-20°C)", "温暖(20-30°C)", "炎热(>30°C)"] = Field(
        description="温度区间分级"
    )
    humidity_range: Literal["干燥(<40%)", "适中(40-70%)", "潮湿(>70%)"] = Field(
        description="湿度区间分级"
    )
    occasion: Literal["日常", "职场", "约会", "社交聚会", "运动", "居家", "正式场合"] = Field(
        description="使用场景（来自问卷 Q1）"
    )
    time_of_day: Literal["清晨", "上午", "下午", "傍晚", "夜间"] = Field(
        description="使用时段（来自问卷 Q8）"
    )
    season: Literal["春", "夏", "秋", "冬"] = Field(
        description="当前季节"
    )
    environmental_coefficient: float = Field(
        ge=0.5,
        le=1.5,
        description="环境系数（0.5~1.5），用于调整配方用量，由 DatabaseManager 计算"
    )


class Agent1Output(BaseModel):
    """Agent1 的完整输出，直接作为 Agent2 的输入"""

    preference_profile: PreferenceProfile = Field(
        description="综合生理数据和问卷得出的用户偏好画像"
    )
    environmental_context: EnvironmentalContext = Field(
        description="综合天气和场合得出的环境上下文"
    )
    scent_keywords: list[str] = Field(
        description="用于数据库检索的香气关键词，如 ['玫瑰', '雪松', '琥珀']"
    )
    analysis_summary: str = Field(
        description="Agent1 的需求分析摘要（100字以内），说明推荐逻辑"
    )


# ──────────────────────────────────────────────────────────────
# Agent 2 输出层
# ──────────────────────────────────────────────────────────────

class FormulaNote(BaseModel):
    """香调结构中单个成分"""

    name: str = Field(description="原料名称，如 佛手柑")
    percentage: float = Field(
        gt=0,
        le=100,
        description="在本层级中的占比（%），同一层级所有成分之和应为 100",
    )
    diffusion_distance: Literal["贴身", "近距离", "中等", "强扩散"] = Field(
        description="该成分的扩散半径级别"
    )
    ingredient_id: Optional[int] = Field(
        default=None,
        description="对应数据库中的精油 ID，自定义原料时可为空",
    )


class PerfumeFormula(BaseModel):
    """完整香水配方，包含前中后三个层次"""

    top_notes: list[FormulaNote] = Field(
        description="前调成分，开瓶后最先散发，持续 15-30 分钟"
    )
    middle_notes: list[FormulaNote] = Field(
        description="中调成分，香水核心，持续 2-4 小时"
    )
    base_notes: list[FormulaNote] = Field(
        description="后调成分，留香最持久，可达 6 小时以上"
    )


class SimilarPerfume(BaseModel):
    """市售香水推荐"""

    brand: str = Field(description="品牌名称，如 Chanel")
    name: str = Field(description="香水全名，如 No.5 Eau de Parfum")
    top_notes: str = Field(description="前调成分，逗号分隔")
    middle_notes: str = Field(description="中调成分，逗号分隔")
    base_notes: str = Field(description="后调成分，逗号分隔")
    reason: str = Field(description="与用户配方相似的原因（30字以内）")


class FinalOutput(BaseModel):
    """Agent2 的最终输出，直接返回给前端"""

    formula: PerfumeFormula = Field(description="生成的香水配方")
    scent_description: str = Field(
        description="面向用户的气味描述文案，生动描绘香水整体感受（150字以内）"
    )
    selection_rationale: str = Field(
        description="配方选择理由，说明如何契合用户生理状态和环境（100字以内）"
    )
    volume_ml: float = Field(
        gt=0,
        description="建议调配总量（毫升）"
    )
    estimated_longevity_hours: float = Field(
        gt=0,
        description="预估留香时长（小时）"
    )
    concentration_percentage: float = Field(
        gt=0,
        le=40,
        description="香精浓度（%）：EDT≈10%，EDP≈15%，香精≈25%"
    )
    similar_perfume: Optional[SimilarPerfume] = Field(
        default=None,
        description="最相似的一款市售香水推荐"
    )
