"""
API 数据模型 (API Models)

职责：
  - 定义所有 API 请求体和响应体的 Pydantic 模型
  - 提供数据校验（类型、长度、枚举值等）
  - 生成 OpenAPI/Swagger 文档所需的字段描述
  - 提供将业务层对象转换为 API 响应的工厂方法

模型分类：
  - Request Models: 请求体数据模型
  - Response Models: 响应体数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


# ──────────────────────────────
# Request Models（请求体）
# ──────────────────────────────

class GenerateRequest(BaseModel):
    """
    香水生成请求体
    （当使用 JSON body 而非 form-data 时使用）
    """
    user_text: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="用户对香水的文字描述",
        examples=["我想要一款适合春天约会的清新花香调香水"],
    )
    occasion: Optional[str] = Field(
        None,
        description="使用场合",
        examples=["约会", "工作", "休闲", "运动"],
    )
    city: Optional[str] = Field(
        None,
        description="城市名，用于查询当前天气辅助推荐",
        examples=["上海", "北京", "广州"],
    )


# ──────────────────────────────
# Response Models（响应体）
# ──────────────────────────────

class IngredientItem(BaseModel):
    """单个原料信息"""
    name: str
    name_cn: str
    category: str               # 前调/中调/后调
    scent_type: str
    intensity_level: int
    ratio: Optional[float]      # 在本配方中的建议比例


class FormulaDetail(BaseModel):
    """香水配方详情"""
    name: str                           # 配方名称
    description: str                    # 配方描述
    top_notes: list[IngredientItem]     # 前调
    middle_notes: list[IngredientItem]  # 中调
    base_notes: list[IngredientItem]    # 后调
    total_volume_ml: float              # 建议总量


class AnalysisDetail(BaseModel):
    """分析过程摘要（供前端展示用）"""
    mood: str
    season_fit: str
    intensity: str
    scent_keywords: list[str]
    occasion_type: str


class GenerateResponse(BaseModel):
    """
    香水生成接口响应体
    包含配方、推荐语、使用建议、分析过程摘要
    """
    success: bool = True
    formula: FormulaDetail
    story: str                          # 香水故事/推荐语
    usage_tips: str                     # 使用建议
    matching_score: float               # 匹配度评分 (0-100)
    analysis_summary: AnalysisDetail    # 分析过程摘要
    weather_info: Optional[dict]        # 天气信息（如有）

    @classmethod
    def from_result(cls, result: Any) -> "GenerateResponse":
        """从业务层 PerfumeGenerationResult 对象构建响应"""
        rec = result.recommendation
        ana = result.analysis

        formula = FormulaDetail(
            name=rec.formula.name,
            description=rec.formula.description,
            top_notes=[IngredientItem(**i.dict()) for i in rec.formula.top_notes],
            middle_notes=[IngredientItem(**i.dict()) for i in rec.formula.middle_notes],
            base_notes=[IngredientItem(**i.dict()) for i in rec.formula.base_notes],
            total_volume_ml=rec.formula.total_volume_ml,
        )

        return cls(
            formula=formula,
            story=rec.story,
            usage_tips=rec.usage_tips,
            matching_score=rec.matching_score,
            analysis_summary=AnalysisDetail(
                mood=ana.mood,
                season_fit=ana.season_fit,
                intensity=ana.intensity,
                scent_keywords=ana.scent_keywords,
                occasion_type=ana.occasion_type,
            ),
            weather_info=result.weather_used,
        )


class IngredientsResponse(BaseModel):
    """原料列表响应体"""
    ingredients: list[dict]
    total: int


class HealthResponse(BaseModel):
    """健康检查响应体"""
    status: str
    message: str
