"""
数据库数据模式定义 (Database Schemas)

职责：
  - 定义 Excel 数据表的字段规范（列名、类型、含义）
  - 提供数据验证工具，确保 Excel 数据格式正确
  - 作为前后端、数据库的统一数据契约

对应的 Excel 文件：
  - ingredients.xlsx  → IngredientSchema
  - formulas.xlsx     → FormulaSchema
  - history.xlsx      → HistorySchema

完整字段说明见 docs/DATABASE_SCHEMA.md
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IngredientSchema(BaseModel):
    """
    香水原料表字段定义
    对应 database/data/ingredients.xlsx
    """
    id: int                         # 原料唯一ID
    name: str                       # 原料英文名（如 Bergamot）
    name_cn: str                    # 原料中文名（如 佛手柑）
    category: str                   # 调性分类：前调/中调/后调
    scent_type: str                 # 气味类型（柑橘/花香/木质/麝香/海洋/辛辣/青草等）
    intensity_level: int = Field(ge=1, le=5)    # 强度等级 1-5
    season_fit: str                 # 适合季节（春/夏/秋/冬/全年）
    description: Optional[str]      # 原料描述
    price_per_ml: Optional[float]   # 每毫升参考价格（元）
    in_stock: bool = True           # 是否有库存


class FormulaSchema(BaseModel):
    """
    参考配方表字段定义
    对应 database/data/formulas.xlsx
    """
    id: int                         # 配方唯一ID
    name: str                       # 配方名称
    style: str                      # 香水风格（清新/浪漫/神秘/商务等）
    season: str                     # 适合季节
    occasion: str                   # 适合场合
    top_note_ids: str               # 前调原料ID列表（逗号分隔）
    middle_note_ids: str            # 中调原料ID列表
    base_note_ids: str              # 后调原料ID列表
    description: Optional[str]      # 配方描述
    created_at: Optional[datetime]  # 创建时间


class HistorySchema(BaseModel):
    """
    生成历史记录表字段定义
    对应 database/data/history.xlsx
    """
    id: Optional[int]               # 记录ID（自增）
    session_id: str                 # 会话ID
    user_text: str                  # 用户原始输入
    occasion: Optional[str]         # 使用场合
    city: Optional[str]             # 查询天气的城市
    mood: str                       # 分析出的情绪倾向
    scent_keywords: str             # 气味关键词（JSON字符串）
    formula_name: str               # 生成的配方名称
    matching_score: float           # 匹配度评分
    created_at: datetime = Field(default_factory=datetime.now)  # 生成时间


# Excel 列名映射（用于验证导入数据的列名是否正确）
INGREDIENT_COLUMNS = [
    "id", "name", "name_cn", "category", "scent_type",
    "intensity_level", "season_fit", "description", "price_per_ml", "in_stock"
]

FORMULA_COLUMNS = [
    "id", "name", "style", "season", "occasion",
    "top_note_ids", "middle_note_ids", "base_note_ids", "description", "created_at"
]


def validate_excel_columns(df_columns: list, expected: list) -> list[str]:
    """
    验证 Excel 文件的列名是否包含必要字段
    返回缺失的列名列表（空列表表示验证通过）
    """
    return [col for col in expected if col not in df_columns]
