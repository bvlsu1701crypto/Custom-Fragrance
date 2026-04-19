"""
数据库管理器 (Database Manager)

职责：
  - 读取和管理 3 张 Excel 数据表（原料、香基概览、香基配方明细）
  - 提供香基查询接口（按家族精确匹配）
  - 提供原料查询接口
  - 支持写入生成历史记录

数据文件位置：
  - database/data/ingredients.xlsx
  - database/data/bases.xlsx
  - database/data/base_details.xlsx
  - database/data/history.xlsx
"""

import math
import os
import pandas as pd
from typing import Any, Optional


def _clean(value: Any) -> Any:
    """把 pandas/numpy 的 NaN/NaT 清洗成 JSON 可序列化的 None。递归处理 dict/list。"""
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, float) and math.isnan(value):
        return None
    if value is pd.NaT:
        return None
    return value


class DatabaseManager:
    """基于 Pandas 读取 Excel 的数据管理器"""

    _instance: Optional["DatabaseManager"] = None

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ingredients_df: Optional[pd.DataFrame] = None
        self._bases_df: Optional[pd.DataFrame] = None
        self._base_details_df: Optional[pd.DataFrame] = None

    @classmethod
    def get_instance(cls, db_path: str) -> "DatabaseManager":
        """全局单例，供 Agent2 等模块复用同一份已加载数据"""
        if cls._instance is None or cls._instance.db_path != db_path:
            cls._instance = cls(db_path)
            cls._instance.load_data()
        return cls._instance

    def load_data(self):
        """加载所有数据到内存（应用启动时调用）"""
        self._ingredients_df = self._read_or_empty("ingredients.xlsx", "原料")
        self._bases_df = self._read_or_empty("bases.xlsx", "香基")
        self._base_details_df = self._read_or_empty("base_details.xlsx", "配方明细")

    def _read_or_empty(self, filename: str, label: str) -> pd.DataFrame:
        path = os.path.join(self.db_path, filename)
        if os.path.exists(path):
            df = pd.read_excel(path)
            print(f"[DB] 加载 {label}: {len(df)} 条 ({filename})")
            return df
        print(f"[DB] 警告: 文件不存在 {path}")
        return pd.DataFrame()

    def _ensure_loaded(self):
        if self._ingredients_df is None or self._bases_df is None or self._base_details_df is None:
            self.load_data()

    def query_bases(
        self,
        family: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        根据家族查询匹配的香基，返回香基列表（每个香基含配方明细）

        Args:
            family: Agent 1 输出的 recommended_family（6 选 1）
            limit: 返回上限。精确匹配不足时从其他家族补充

        Returns:
            list[dict]，每个 dict 形如:
              {
                "id": "B01", "name": "佛手柑空气", "family": "柑橘清新",
                "style": "...", "formula_text": "...",
                "high_impact_notes": "...", "test_suggestion": "...",
                "details": [{base_id, ingredient, ingredient_id, parts, role, ...}, ...]
              }
        """
        self._ensure_loaded()
        if self._bases_df is None or self._bases_df.empty:
            return []

        df = self._bases_df

        # 精确匹配家族
        if family and "family" in df.columns:
            matched = df[df["family"] == family]
            rest = df[df["family"] != family]
            combined = pd.concat([matched, rest], ignore_index=True)
        else:
            combined = df

        selected = combined.head(limit)
        return [self._attach_details(row) for row in selected.to_dict(orient="records")]

    def _attach_details(self, base_row: dict) -> dict:
        """给单个香基附上配方明细"""
        details: list[dict] = []
        if self._base_details_df is not None and not self._base_details_df.empty:
            rows = self._base_details_df[self._base_details_df["base_id"] == base_row["id"]]
            details = rows.to_dict(orient="records")
        return _clean({**base_row, "details": details})

    def get_base_with_details(self, base_id: str) -> Optional[dict]:
        """获取单个香基的完整信息 + 配方明细"""
        self._ensure_loaded()
        if self._bases_df is None or self._bases_df.empty:
            return None
        match = self._bases_df[self._bases_df["id"] == base_id]
        if match.empty:
            return None
        return self._attach_details(match.iloc[0].to_dict())

    def get_all_ingredients(self) -> list[dict]:
        """获取全部原料列表（供 /api/ingredients 使用）"""
        self._ensure_loaded()
        if self._ingredients_df is None or self._ingredients_df.empty:
            return []
        return _clean(self._ingredients_df.to_dict(orient="records"))

    def get_all_bases(self) -> list[dict]:
        """获取全部香基概览（不含明细）"""
        self._ensure_loaded()
        if self._bases_df is None or self._bases_df.empty:
            return []
        return _clean(self._bases_df.to_dict(orient="records"))

    def save_generation_history(self, record: dict):
        """保存一次香水生成记录到 history.xlsx"""
        history_path = os.path.join(self.db_path, "history.xlsx")
        new_row = pd.DataFrame([record])

        if os.path.exists(history_path):
            existing = pd.read_excel(history_path)
            updated = pd.concat([existing, new_row], ignore_index=True)
        else:
            updated = new_row

        updated.to_excel(history_path, index=False)
        print(f"[DB] 已保存生成记录，共 {len(updated)} 条历史")
