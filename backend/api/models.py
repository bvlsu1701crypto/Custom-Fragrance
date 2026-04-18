"""
API 数据模型 (API Models)

职责：
  - 定义所有 API 请求体和响应体的 Pydantic 模型
  - 提供数据校验（类型、长度、枚举值等）
  - 生成 OpenAPI/Swagger 文档所需的字段描述
  - 提供将业务层对象转换为 API 响应的工厂方法
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


# ──────────────────────────────
# Request Models
# ──────────────────────────────

class GenerateRequest(BaseModel):
    """香水生成请求体（JSON body 可选）"""
    user_text: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="用户对香水的文字描述",
        examples=["我想要一款适合春天约会的清新花香调香水"],
    )
    occasion: Optional[str] = Field(None, examples=["约会", "工作", "休闲", "运动"])
    city: Optional[str] = Field(None, examples=["上海", "北京", "广州"])


# ──────────────────────────────
# Response Models
# ──────────────────────────────

class BaseIngredientItem(BaseModel):
    """香基中的单个原料（用于展示）"""
    ingredient: str
    ingredient_id: int
    parts: int
    role: str


class BaseRecommendationItem(BaseModel):
    """单个香基推荐的响应模型"""
    base_id: str
    base_name: str
    family: str
    style: str
    ingredients: list[BaseIngredientItem]
    high_impact_notes: Optional[str] = None
    test_suggestion: Optional[str] = None
    story: str
    usage_tips: str
    matching_score: float


class AnalysisDetail(BaseModel):
    """分析过程摘要"""
    mood: str
    season_fit: str
    intensity: str
    scent_keywords: list[str]
    occasion_type: str
    recommended_family: str


class GenerateResponse(BaseModel):
    """香水生成接口响应体（香基推荐模式）"""
    success: bool = True
    primary: BaseRecommendationItem
    alternative: Optional[BaseRecommendationItem] = None
    personalization_tips: str
    analysis_summary: AnalysisDetail
    weather_info: Optional[dict] = None

    @classmethod
    def from_result(cls, result: Any) -> "GenerateResponse":
        """从业务层 PerfumeGenerationResult 对象构建响应"""
        rec = result.recommendation
        ana = result.analysis

        def to_item(base_rec) -> BaseRecommendationItem:
            return BaseRecommendationItem(
                base_id=base_rec.base_id,
                base_name=base_rec.base_name,
                family=base_rec.family,
                style=base_rec.style,
                ingredients=[BaseIngredientItem(**i.model_dump()) for i in base_rec.ingredients],
                high_impact_notes=base_rec.high_impact_notes,
                test_suggestion=base_rec.test_suggestion,
                story=base_rec.story,
                usage_tips=base_rec.usage_tips,
                matching_score=base_rec.matching_score,
            )

        return cls(
            primary=to_item(rec.primary),
            alternative=to_item(rec.alternative) if rec.alternative else None,
            personalization_tips=rec.personalization_tips,
            analysis_summary=AnalysisDetail(
                mood=ana.mood,
                season_fit=ana.season_fit,
                intensity=ana.intensity,
                scent_keywords=ana.scent_keywords,
                occasion_type=ana.occasion_type,
                recommended_family=ana.recommended_family,
            ),
            weather_info=result.weather_used,
        )


class IngredientsResponse(BaseModel):
    """原料列表响应体"""
    ingredients: list[dict]
    total: int


class BasesResponse(BaseModel):
    """香基列表响应体"""
    bases: list[dict]
    total: int


class HealthResponse(BaseModel):
    """健康检查响应体"""
    status: str
    message: str
