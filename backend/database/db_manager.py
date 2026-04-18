"""
数据库管理器 (Database Manager)

单例模式，应用启动时一次性加载 Excel 文件并缓存为 JSON。
后续查询直接读内存，避免重复 I/O。

数据文件（位于 database/data/）：
  - perfume_formula_database.xlsx        香水配方与原料主表
  - social_distance_data.xlsx            社交距离与扩散系数表
  - essential_oils_diffusion_comparison.xlsx  精油扩散对比参数表

JSON 缓存（同目录自动生成）：
  - perfume_formula_database.json
  - social_distance_data.json
  - essential_oils_diffusion_comparison.json
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# 文件名常量
# ──────────────────────────────────────────────────────────────

_FILE_FORMULA = "perfume_formula_database"
_FILE_SOCIAL  = "social_distance_data"
_FILE_OILS    = "essential_oils_diffusion_comparison"

_ALL_FILES = [_FILE_FORMULA, _FILE_SOCIAL, _FILE_OILS]


class DatabaseManager:
    """
    数据库管理器（线程安全单例）

    使用方式：
        db = DatabaseManager.get_instance("database/data")
        oils = db.query_oils_by_scent_family(["花香", "木质"])
    """

    _instance: Optional[DatabaseManager] = None
    _lock: threading.Lock = threading.Lock()

    # ── 单例工厂 ───────────────────────────────

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        # 内存缓存：key = 文件名常量，value = list[dict]
        self._cache: dict[str, list[dict]] = {}
        self._load_all()

    @classmethod
    def get_instance(cls, data_dir: str = "database/data") -> DatabaseManager:
        """获取全局单例，首次调用时初始化并加载数据"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(data_dir)
        return cls._instance

    # ── 数据加载 ───────────────────────────────

    def _load_all(self) -> None:
        """启动时加载全部数据表"""
        os.makedirs(self.data_dir, exist_ok=True)
        for name in _ALL_FILES:
            try:
                self._cache[name] = self._load_table(name)
                logger.info("[DB] 加载 %s：%d 条记录", name, len(self._cache[name]))
            except Exception as exc:
                logger.warning("[DB] 加载 %s 失败：%s", name, exc)
                self._cache[name] = []

    def _load_table(self, name: str) -> list[dict]:
        """
        优先读 JSON 缓存；JSON 不存在则读 Excel 并生成 JSON。
        返回 list[dict]。
        """
        json_path  = os.path.join(self.data_dir, f"{name}.json")
        excel_path = os.path.join(self.data_dir, f"{name}.xlsx")

        # 优先使用 JSON 缓存
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("[DB] 从 JSON 缓存加载 %s", name)
            return data

        # 读 Excel，转换为 JSON 保存
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path, engine="openpyxl")
            # NaN → None，保证 JSON 可序列化
            records = df.where(pd.notna(df), None).to_dict(orient="records")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            logger.info("[DB] Excel→JSON 转换完成：%s", json_path)
            return records

        logger.warning("[DB] 数据文件不存在（xlsx/json 均未找到）：%s", name)
        return []

    def reload(self) -> None:
        """强制重新从 Excel 加载并刷新 JSON 缓存（用于数据更新后）"""
        # 删除旧 JSON，重新加载
        for name in _ALL_FILES:
            json_path = os.path.join(self.data_dir, f"{name}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
        self._load_all()
        logger.info("[DB] 数据已重新加载")

    # ── 工具方法 ───────────────────────────────

    def _get(self, table: str) -> list[dict]:
        return self._cache.get(table, [])

    @staticmethod
    def _str_contains(value: Any, keywords: list[str]) -> bool:
        """判断字段值是否包含任意一个关键词（不区分大小写）"""
        if not isinstance(value, str):
            return False
        low = value.lower()
        return any(kw.lower() in low for kw in keywords)

    # ── 查询方法 ───────────────────────────────

    def query_oils_by_scent_family(
        self,
        scent_families: list[str],
        note_type: Optional[str] = None,
        limit: int = 30,
    ) -> list[dict]:
        """
        按香调族群查询精油

        Args:
            scent_families: 香调族群关键词列表，如 ['花香', '木质']
            note_type:      调性筛选，'前调' / '中调' / '后调'，None 表示不限
            limit:          最大返回条数

        Returns:
            匹配的精油记录列表
        """
        records = self._get(_FILE_FORMULA)
        if not records:
            logger.warning("[DB] query_oils_by_scent_family：数据表为空")
            return []

        results = []
        for row in records:
            # 匹配香调族群
            family_val = row.get("scent_family") or row.get("香调族群") or ""
            if not self._str_contains(family_val, scent_families):
                continue
            # 可选：筛选调性
            if note_type:
                note_val = row.get("note_type") or row.get("调性") or ""
                if note_type not in str(note_val):
                    continue
            results.append(row)
            if len(results) >= limit:
                break

        logger.debug("[DB] query_oils_by_scent_family(%s) → %d 条", scent_families, len(results))
        return results

    def query_oils_by_diffusion_range(
        self,
        min_distance: float,
        max_distance: float,
        unit: str = "cm",
    ) -> list[dict]:
        """
        按扩散距离范围查询精油

        Args:
            min_distance: 最小扩散距离
            max_distance: 最大扩散距离
            unit:         单位，'cm' 或 'm'

        Returns:
            在扩散范围内的精油记录列表
        """
        records = self._get(_FILE_OILS)
        if not records:
            logger.warning("[DB] query_oils_by_diffusion_range：扩散对比表为空")
            return []

        results = []
        for row in records:
            raw = row.get("diffusion_distance") or row.get("扩散距离") or row.get("diffusion_cm")
            if raw is None:
                continue
            try:
                distance = float(raw)
                # 单位统一为 cm
                if unit == "m":
                    distance *= 100
                if min_distance <= distance <= max_distance:
                    results.append(row)
            except (ValueError, TypeError):
                continue

        logger.debug(
            "[DB] query_oils_by_diffusion_range(%.1f-%.1f %s) → %d 条",
            min_distance, max_distance, unit, len(results),
        )
        return results

    def get_oil_by_id(self, oil_id: int) -> Optional[dict]:
        """
        按精油 ID 查询单条记录

        Args:
            oil_id: 精油唯一 ID

        Returns:
            精油记录 dict，不存在时返回 None
        """
        for row in self._get(_FILE_FORMULA):
            row_id = row.get("id") or row.get("ID") or row.get("精油ID")
            try:
                if int(row_id) == oil_id:
                    return row
            except (ValueError, TypeError):
                continue

        logger.debug("[DB] get_oil_by_id(%d)：未找到", oil_id)
        return None

    def calculate_environmental_coefficient(
        self,
        temperature: float,
        humidity: int,
        occasion: str,
    ) -> float:
        """
        根据温湿度和使用场景计算环境系数

        环境系数用于调整配方中各成分的用量：
          - 高温高湿 → 系数偏低，建议减少用量
          - 低温干燥 → 系数偏高，建议增加用量

        Args:
            temperature: 当前温度（摄氏度）
            humidity:    当前湿度（%）
            occasion:    使用场合，如 '约会' / '职场' / '运动'

        Returns:
            环境系数，范围 0.5 ~ 1.5
        """
        # ── 温度系数（高温降低用量，低温增加用量）────
        if temperature >= 30:
            temp_coef = 0.7
        elif temperature >= 20:
            temp_coef = 0.9
        elif temperature >= 10:
            temp_coef = 1.1
        else:
            temp_coef = 1.3

        # ── 湿度系数（高湿加速扩散，适当减少）────────
        if humidity >= 70:
            hum_coef = 0.85
        elif humidity >= 40:
            hum_coef = 1.0
        else:
            hum_coef = 1.15

        # ── 场合系数（封闭/私密场合减少用量）─────────
        occasion_map = {
            "日常":   1.0,
            "职场":   0.8,   # 封闭办公室，不宜过浓
            "约会":   1.1,
            "社交聚会": 1.2,
            "运动":   0.7,   # 运动出汗加速挥发，减量
            "居家":   0.9,
            "正式场合": 0.85,
        }
        occ_coef = occasion_map.get(occasion, 1.0)

        coefficient = round(temp_coef * hum_coef * occ_coef, 3)
        # 限制在合理范围内
        coefficient = max(0.5, min(1.5, coefficient))

        logger.debug(
            "[DB] 环境系数计算：temp=%.1f hum=%d occasion=%s → %.3f",
            temperature, humidity, occasion, coefficient,
        )
        return coefficient

    def get_base_formula_recommendations(
        self,
        scent_families: list[str],
        occasion: str,
        season: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        根据香调偏好、场合和季节推荐基础配方

        Args:
            scent_families: 偏好香调族群列表
            occasion:       使用场合
            season:         季节（春/夏/秋/冬）
            limit:          最大返回配方数

        Returns:
            推荐的基础配方列表，按匹配度降序排列
        """
        records = self._get(_FILE_FORMULA)
        if not records:
            logger.warning("[DB] get_base_formula_recommendations：配方表为空")
            return []

        scored: list[tuple[int, dict]] = []

        for row in records:
            score = 0

            # 香调族群匹配（每匹配一个 +2 分）
            family_val = str(row.get("scent_family") or row.get("香调族群") or "")
            for family in scent_families:
                if family.lower() in family_val.lower():
                    score += 2

            # 场合匹配（+3 分）
            occ_val = str(row.get("occasion") or row.get("场合") or "")
            if occasion.lower() in occ_val.lower():
                score += 3

            # 季节匹配（+2 分）
            season_val = str(row.get("season") or row.get("季节") or "")
            if season in season_val or "全年" in season_val:
                score += 2

            if score > 0:
                scored.append((score, row))

        # 按分数降序，取前 N 条
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [row for _, row in scored[:limit]]

        logger.debug(
            "[DB] get_base_formula_recommendations(%s, %s, %s) → %d 条",
            scent_families, occasion, season, len(results),
        )
        return results
