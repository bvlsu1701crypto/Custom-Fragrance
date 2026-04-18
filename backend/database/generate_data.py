"""
数据转换脚本 (Data Generation Script)

从 `backend/database/30个香基规划.xlsx` 读取 5 个 sheet，
输出归一化后的 3 个数据文件到 `backend/database/data/`：
  - ingredients.xlsx   38 种原料（含功能/强度/优先级）
  - bases.xlsx         30 个香基概览
  - base_details.xlsx  271 行配方明细（含 ingredient_id）

运行方式：
  cd backend && python database/generate_data.py
"""

import os
import sys
import pandas as pd


SOURCE_XLSX = os.path.join(os.path.dirname(__file__), "30个香基规划.xlsx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")


# 38 种原料的规范名映射
# key = 在任何 sheet 中出现的名称变体, value = 原料 ID (1-38)
NAME_TO_ID = {
    # 1. 佛手柑油
    "佛手柑油": 1, "BERGAMOT OIL": 1, "Bergamot Oil": 1,
    # 2. Iso E Super
    "Iso E Super": 2, "ISO E SUPER": 2,
    # 3. 芳樟醇
    "芳樟醇": 3, "Natural Linalool": 3,
    # 4. Hedione / 二氢茉莉酮酸甲酯
    "二氢茉莉酮酸甲酯": 4, "Hedione": 4,
    # 5. Cis-3-Hexen-1-ol / 顺-3-己烯醇
    "顺-3-己烯醇": 5, "Cis-3-Hexen-1-ol": 5,
    # 6. Galaxolide / 佳乐麝香 75%
    "佳乐麝香 75%": 6, "Galaxolide": 6,
    # 7. Benzoin Resinoid / 安息香浸膏
    "安息香浸膏": 7, "Benzoin Resinoid Sumatra": 7, "Benzoin Resinoid": 7,
    # 8. Phenethyl Alcohol / 苯乙醇
    "苯乙醇": 8, "Phenethyl Alcohol": 8,
    # 9. Melonal / 甜瓜醛
    "甜瓜醛": 9, "Melonal": 9,
    # 10. Gamma Undecalactone / 丙位十一内酯
    "丙位十一内酯": 10, "Gamma Undecalactone": 10,
    # 11. Cashmeran / 开司米酮
    "开司米酮": 11, "Cashmeran": 11,
    # 12. Calone / 卡龙
    "卡龙": 12, "Calone": 12,
    # 13. Ionone Alpha / 甲位紫罗兰酮
    "甲位紫罗兰酮": 13, "Ionone Alpha": 13,
    # 14. Ethyl Maltol / 乙基麦芽酚
    "乙基麦芽酚": 14, "Ethyl Maltol": 14,
    # 15. Exaltolide Total / 环十五内酯
    "环十五内酯": 15, "Exaltolide Total": 15,
    # 16. Eugenol / 丁香酚
    "丁香酚": 16, "Eugenol USP": 16, "Eugenol": 16,
    # 17. Cedarwood / 雪松精油 TE 级
    "雪松精油 TE 级": 17, "CEDARWOOD SUPER RECT": 17, "Cedarwood Super Rect": 17,
    # 18. Benzyl Acetate / 乙酸苄酯
    "乙酸苄酯": 18, "Benzyl Acetate": 18,
    # 19. Lemon Terpene / 柠檬萜
    "柠檬萜": 19, "LEMON TERPENE": 19, "Lemon Terpene": 19,
    # 20. Citral N / 天然柠檬醛
    "天然柠檬醛": 20, "CITRAL N": 20, "Citral N": 20,
    # 21. Birch Oil / 桦木油
    "桦木油": 21, "Birch Oil": 21,
    # 22. Ethyl Vanillin / 乙基香兰素
    "乙基香兰素": 22, "Ethyl Vanillin": 22,
    # 23. Coumarin / 香豆素
    "香豆素": 23, "Coumarin": 23,
    # 24. Ionone Beta / 乙位紫罗兰酮
    "乙位紫罗兰酮": 24, "Ionone Beta": 24,
    # 25. Patchouli Alcohol / 广藿香醇
    "广藿香醇": 25, "Patchouli Alcohol": 25,
    # 26. Ethyl 2-methylbutyrate / 2-甲基丁酸乙酯
    "2-甲基丁酸乙酯": 26, "Ethyl 2-methylbutyrate": 26,
    # 27. Benzyl Benzoate / 苯甲酸苄酯
    "苯甲酸苄酯": 27, "Benzyl Benzoate": 27,
    # 28. Habanolide / 哈巴内酯
    "哈巴内酯": 28, "Habanolide": 28,
    # 29. Zenolide
    "Zenolide": 29, "ZENOLIDE": 29,
    # 30. Basil Oil / 罗勒油
    "罗勒油": 30, "Basil Oil Linalool Type": 30, "Basil Oil": 30,
    # 31. Indole / 吲哚
    "吲哚": 31, "Indole": 31,
    # 32. Peru Resinoid / 秘鲁香脂浸膏
    "秘鲁香脂浸膏": 32, "Peru Resinoid": 32,
    # 33. Green Tea / 绿茶香基
    "绿茶香基": 33, "GREEN TEA": 33, "Green Tea": 33,
    # 34. Raspberry Ketone / 覆盆子酮
    "覆盆子酮": 34, "Raspberry Ketone": 34,
    # 35. Furaneol / 呋喃酮
    "呋喃酮": 35, "Furaneol": 35,
    # 36. Musk 105 / 麝香 105
    "麝香 105": 36, "Musk R; 11-Oxahexadecanolide": 36, "Musk 105": 36,
    # 37. Orris GIVCO 204/2 / 鸢尾香基
    "鸢尾香基": 37, "Orris GIVCO 204/2": 37,
    # 38. High Cis Hedione / 高顺式 HEDIONE
    "高顺式 HEDIONE": 38, "HIGH CIS HEDIONE": 38, "High Cis Hedione": 38,
}


# "核心原料池" 中的组合条目，需要拆分到多个 ingredient_id
COMBO_ROW_SPLITS = {
    "Bergamot + Lemon Terpene": [1, 19],
    "Birch Oil / Indole / Eugenol": [21, 31, 16],
}


def normalize_name(name: str) -> int:
    """将任意形式的原料名归一化为 ingredient_id；找不到则抛异常"""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        raise ValueError(f"原料名为空")
    key = str(name).strip()
    if key in NAME_TO_ID:
        return NAME_TO_ID[key]
    raise KeyError(f"原料名 '{key}' 不在 NAME_TO_ID 映射表中，请补充")


def build_ingredients(identified_df: pd.DataFrame, core_df: pd.DataFrame) -> pd.DataFrame:
    """合并"已识别原料" + "核心原料池"，生成 ingredients.xlsx"""

    # Step 1: 用"已识别原料" 38 行作为基准
    base = identified_df.rename(columns={
        "序号": "id",
        "原料": "name_cn",
        "英文名": "name",
        "类别": "material_type",
        "建议级别": "caution_level",
        "备注": "description",
    })[["id", "name", "name_cn", "material_type", "caution_level", "description"]].copy()

    # Step 2: 构建 ingredient_id → {function, intensity, priority, usage} 的字典
    # "核心原料池"中每行的"原料"名可能是英文或中文，通过 NAME_TO_ID 归一化
    enrich: dict[int, dict] = {}
    for _, row in core_df.iterrows():
        raw_name = str(row["原料"]).strip()
        # 处理组合条目
        if raw_name in COMBO_ROW_SPLITS:
            ids = COMBO_ROW_SPLITS[raw_name]
        else:
            try:
                ids = [normalize_name(raw_name)]
            except KeyError as e:
                print(f"[WARN] 核心原料池未识别: {e}")
                continue
        payload = {
            "function": row.get("功能"),
            "intensity": row.get("强度"),
            "priority": row.get("优先级"),
            "usage": row.get("建议用途"),
        }
        for ing_id in ids:
            enrich[ing_id] = payload

    # Step 3: left join
    base["function"] = base["id"].map(lambda i: enrich.get(i, {}).get("function"))
    base["intensity"] = base["id"].map(lambda i: enrich.get(i, {}).get("intensity"))
    base["priority"] = base["id"].map(lambda i: enrich.get(i, {}).get("priority"))
    base["usage"] = base["id"].map(lambda i: enrich.get(i, {}).get("usage"))
    base["in_stock"] = True

    # 调整列顺序
    return base[[
        "id", "name", "name_cn", "material_type",
        "caution_level", "description",
        "function", "intensity", "priority", "usage",
        "in_stock",
    ]]


def build_bases(bases_df: pd.DataFrame) -> pd.DataFrame:
    """直接从"30个香基"生成 bases.xlsx"""
    return bases_df.rename(columns={
        "编号": "id",
        "香基名称": "name",
        "家族": "family",
        "风格说明": "style",
        "配方（100份）": "formula_text",
        "高影响原料": "high_impact_notes",
        "试香建议": "test_suggestion",
    })[["id", "name", "family", "style", "formula_text", "high_impact_notes", "test_suggestion"]]


def build_base_details(detail_df: pd.DataFrame) -> pd.DataFrame:
    """从"配方明细"生成 base_details.xlsx，增加 ingredient_id 列"""
    df = detail_df.rename(columns={
        "编号": "base_id",
        "香基名称": "base_name",
        "家族": "family",
        "原料": "ingredient",
        "份数": "parts",
        "角色": "role",
    }).copy()

    # 为每行加 ingredient_id，找不到则抛异常（确保 0 遗漏）
    missing: list[str] = []
    ids: list[int] = []
    for _, row in df.iterrows():
        try:
            ids.append(normalize_name(row["ingredient"]))
        except KeyError:
            missing.append(str(row["ingredient"]))
            ids.append(-1)
    if missing:
        raise RuntimeError(
            f"配方明细中有 {len(missing)} 种原料未在 NAME_TO_ID 中: {set(missing)}"
        )
    df["ingredient_id"] = ids
    return df[["base_id", "base_name", "family", "ingredient", "ingredient_id", "parts", "role"]]


def main():
    if not os.path.exists(SOURCE_XLSX):
        print(f"[ERROR] 源文件不存在: {SOURCE_XLSX}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[1/3] 读取源文件: {SOURCE_XLSX}")
    identified_df = pd.read_excel(SOURCE_XLSX, sheet_name="已识别原料")
    core_df = pd.read_excel(SOURCE_XLSX, sheet_name="核心原料池")
    bases_df = pd.read_excel(SOURCE_XLSX, sheet_name="30个香基")
    detail_df = pd.read_excel(SOURCE_XLSX, sheet_name="配方明细")

    print(f"  已识别原料: {len(identified_df)} 行")
    print(f"  核心原料池: {len(core_df)} 行")
    print(f"  30个香基:    {len(bases_df)} 行")
    print(f"  配方明细:    {len(detail_df)} 行")

    print("[2/3] 转换数据")
    ingredients = build_ingredients(identified_df, core_df)
    bases = build_bases(bases_df)
    details = build_base_details(detail_df)

    print("[3/3] 写入输出文件")
    ing_path = os.path.join(OUTPUT_DIR, "ingredients.xlsx")
    base_path = os.path.join(OUTPUT_DIR, "bases.xlsx")
    detail_path = os.path.join(OUTPUT_DIR, "base_details.xlsx")
    ingredients.to_excel(ing_path, index=False)
    bases.to_excel(base_path, index=False)
    details.to_excel(detail_path, index=False)

    print(f"\n[OK] 生成完成:")
    print(f"  {ing_path}  ({len(ingredients)} 行)")
    print(f"  {base_path}  ({len(bases)} 行)")
    print(f"  {detail_path}  ({len(details)} 行)")

    # 质量统计
    enriched_count = ingredients["function"].notna().sum()
    print(f"\n[统计] 原料表中有 function 字段的行: {enriched_count}/{len(ingredients)}")


if __name__ == "__main__":
    main()
