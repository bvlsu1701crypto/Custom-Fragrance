"""
数据库数据模式定义 (Database Schemas)

职责：
  - 定义 Excel 数据表的字段规范（列名、类型、含义）
  - 作为前后端、数据库的统一数据契约

对应的 Excel 文件：
  - ingredients.xlsx    → IngredientSchema   (38 种原料)
  - bases.xlsx          → BaseSchema         (30 个香基概览)
  - base_details.xlsx   → BaseDetailSchema   (271 行配方明细)
  - history.xlsx        → HistorySchema      (生成历史)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# 6 个香基家族（枚举值）
BASE_FAMILIES = [
    "柑橘清新",
    "绿意水生",
    "花香粉感",
    "木质琥珀",
    "甜感美食",
    "树脂辛香",
]


class IngredientSchema(BaseModel):
    """
    香水原料表字段定义
    对应 database/data/ingredients.xlsx
    """
    id: int                         # 原料唯一 ID (1-38)
    name: str                       # 原料英文名
    name_cn: str                    # 原料中文名
    material_type: str              # 植物香料/合成香料/食用香料/其他香料
    caution_level: str              # 推荐/谨慎/辅助
    description: Optional[str] = None   # 备注
    function: Optional[str] = None      # 功能（柑橘顶香/透明木质...）
    intensity: Optional[str] = None     # 强度（高/中高/中/高影响/功能料）
    priority: Optional[str] = None      # 优先级（A/B/C）
    usage: Optional[str] = None         # 建议用途
    in_stock: bool = True


class BaseSchema(BaseModel):
    """
    香基概览表字段定义
    对应 database/data/bases.xlsx
    """
    id: str                         # B01-B30
    name: str                       # 香基名称
    family: str                     # 6 个家族之一
    style: str                      # 风格说明
    formula_text: str               # 配方（100份）原始文本
    high_impact_notes: Optional[str] = None     # 高影响原料
    test_suggestion: Optional[str] = None       # 试香建议


class BaseDetailSchema(BaseModel):
    """
    香基配方明细字段定义
    对应 database/data/base_details.xlsx
    """
    base_id: str                    # 指向 bases.id
    base_name: str
    family: str
    ingredient: str                 # 原料原始名（用于展示）
    ingredient_id: int              # 指向 ingredients.id
    parts: int                      # 份数（总和为 100）
    role: str                       # 自由文本（骨架/空气感/主顶香/连接/底托/留香...）


class HistorySchema(BaseModel):
    """
    生成历史记录表字段定义
    对应 database/data/history.xlsx
    """
    id: Optional[int] = None
    session_id: str
    user_text: str
    occasion: Optional[str] = None
    city: Optional[str] = None
    mood: str
    scent_keywords: str             # JSON 字符串
    recommended_family: Optional[str] = None
    primary_base_id: Optional[str] = None
    primary_base_name: Optional[str] = None
    matching_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)


# Excel 列名（用于校验导入数据列是否完整）
INGREDIENT_COLUMNS = [
    "id", "name", "name_cn", "material_type",
    "caution_level", "description",
    "function", "intensity", "priority", "usage",
    "in_stock",
]

BASE_COLUMNS = [
    "id", "name", "family", "style",
    "formula_text", "high_impact_notes", "test_suggestion",
]

BASE_DETAIL_COLUMNS = [
    "base_id", "base_name", "family",
    "ingredient", "ingredient_id", "parts", "role",
]


def validate_excel_columns(df_columns: list, expected: list) -> list[str]:
    """验证 Excel 列名是否包含所有必要字段；返回缺失列"""
    return [col for col in expected if col not in df_columns]
