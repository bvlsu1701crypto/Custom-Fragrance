"""
数据库管理器 (Database Manager)

职责：
  - 读取和管理 Excel 数据表（香水原料库、配方库）
  - 提供原料查询接口，支持按气味类型、季节、强度筛选
  - 支持将 Excel 数据加载到内存，提升查询性能
  - 提供数据写入能力（记录生成历史）

数据文件位置：
  - database/data/ingredients.xlsx   香水原料表
  - database/data/formulas.xlsx      参考配方表
  - database/data/history.xlsx       生成历史记录

Excel 表字段说明见 docs/DATABASE_SCHEMA.md
"""

import pandas as pd
import os
from typing import Optional
from database.schemas import IngredientSchema, FormulaSchema


class DatabaseManager:
    """
    数据库管理器
    基于 Pandas 读取 Excel 文件，提供结构化数据查询能力
    """

    def __init__(self, db_path: str):
        """
        初始化数据库管理器

        Args:
            db_path: Excel 数据文件所在的文件夹路径
        """
        self.db_path = db_path
        self._ingredients_df: Optional[pd.DataFrame] = None
        self._formulas_df: Optional[pd.DataFrame] = None

    def load_data(self):
        """加载所有 Excel 数据到内存（应用启动时调用）"""
        ingredients_path = os.path.join(self.db_path, "ingredients.xlsx")
        formulas_path = os.path.join(self.db_path, "formulas.xlsx")

        if os.path.exists(ingredients_path):
            self._ingredients_df = pd.read_excel(ingredients_path)
            print(f"[DB] 加载原料数据: {len(self._ingredients_df)} 条")
        else:
            print(f"[DB] 警告: 原料数据文件不存在 {ingredients_path}")
            self._ingredients_df = pd.DataFrame()

        if os.path.exists(formulas_path):
            self._formulas_df = pd.read_excel(formulas_path)
            print(f"[DB] 加载配方数据: {len(self._formulas_df)} 条")
        else:
            self._formulas_df = pd.DataFrame()

    def query_ingredients(
        self,
        scent_keywords: list[str],
        season: Optional[str] = None,
        intensity: Optional[str] = None,
        limit: int = 30,
    ) -> list[dict]:
        """
        根据气味关键词和筛选条件查询适合的原料

        Args:
            scent_keywords: 气味关键词列表（来自 Agent 1）
            season: 季节适配筛选
            intensity: 香气强度筛选
            limit: 返回数量上限

        Returns:
            匹配的原料列表（dict 格式）
        """
        if self._ingredients_df is None or self._ingredients_df.empty:
            self.load_data()

        df = self._ingredients_df.copy()

        if df.empty:
            return []

        # 按气味关键词过滤（模糊匹配 scent_type 列）
        if scent_keywords and "scent_type" in df.columns:
            pattern = "|".join(scent_keywords)
            mask = df["scent_type"].str.contains(pattern, case=False, na=False)
            filtered = df[mask]
            # 如果过滤后太少，补充一些基础原料
            if len(filtered) < 10:
                filtered = pd.concat([filtered, df.sample(min(10, len(df)))]).drop_duplicates()
            df = filtered

        # 按强度筛选
        intensity_map = {"淡": (1, 2), "中": (2, 4), "浓": (4, 5)}
        if intensity and intensity in intensity_map and "intensity_level" in df.columns:
            lo, hi = intensity_map[intensity]
            df = df[df["intensity_level"].between(lo, hi)]

        # 返回前 N 条，转换为 dict 列表
        return df.head(limit).to_dict(orient="records")

    def save_generation_history(self, record: dict):
        """
        保存一次香水生成记录到 history.xlsx

        Args:
            record: 包含用户输入、分析结果、配方等信息的字典
        """
        history_path = os.path.join(self.db_path, "history.xlsx")

        new_row = pd.DataFrame([record])

        if os.path.exists(history_path):
            existing = pd.read_excel(history_path)
            updated = pd.concat([existing, new_row], ignore_index=True)
        else:
            updated = new_row

        updated.to_excel(history_path, index=False)
        print(f"[DB] 已保存生成记录，当前共 {len(updated)} 条历史")

    def get_all_ingredients(self) -> list[dict]:
        """获取全部原料列表"""
        if self._ingredients_df is None:
            self.load_data()
        return self._ingredients_df.to_dict(orient="records") if not self._ingredients_df.empty else []
