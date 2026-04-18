# 数据库结构文档

所有数据以 Excel 文件形式存储在 `backend/database/data/` 目录下。

---

## 1. 原料表 `ingredients.xlsx`

存储香水调香原料的基础信息。

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | ✅ | 原料唯一ID（自增） |
| `name` | string | ✅ | 原料英文名（如 Bergamot） |
| `name_cn` | string | ✅ | 原料中文名（如 佛手柑） |
| `category` | string | ✅ | 调性分类：`前调` / `中调` / `后调` |
| `scent_type` | string | ✅ | 气味类型（柑橘/花香/木质/麝香/海洋/辛辣/青草/果香/东方/皮革） |
| `intensity_level` | int(1-5) | ✅ | 香气强度等级，1最淡，5最浓 |
| `season_fit` | string | ✅ | 适合季节：`春` / `夏` / `秋` / `冬` / `全年` |
| `description` | string | ❌ | 原料描述和香气特点 |
| `price_per_ml` | float | ❌ | 每毫升参考价格（元） |
| `in_stock` | bool | ✅ | 是否有库存，默认 `TRUE` |

**示例数据**:
| id | name | name_cn | category | scent_type | intensity_level | season_fit |
|----|------|---------|----------|------------|-----------------|------------|
| 1 | Bergamot | 佛手柑 | 前调 | 柑橘 | 3 | 春夏 |
| 2 | Rose | 玫瑰 | 中调 | 花香 | 3 | 全年 |
| 3 | Sandalwood | 檀香 | 后调 | 木质 | 4 | 秋冬 |
| 4 | Musk | 麝香 | 后调 | 麝香 | 2 | 全年 |
| 5 | Jasmine | 茉莉 | 中调 | 花香 | 4 | 春夏 |

---

## 2. 参考配方表 `formulas.xlsx`

存储预设的香水参考配方。

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | ✅ | 配方唯一ID |
| `name` | string | ✅ | 配方名称 |
| `style` | string | ✅ | 香水风格（清新/浪漫/神秘/商务/运动） |
| `season` | string | ✅ | 适合季节 |
| `occasion` | string | ✅ | 适合场合 |
| `top_note_ids` | string | ✅ | 前调原料ID，逗号分隔（如 "1,5"） |
| `middle_note_ids` | string | ✅ | 中调原料ID |
| `base_note_ids` | string | ✅ | 后调原料ID |
| `description` | string | ❌ | 配方描述 |
| `created_at` | datetime | ❌ | 创建时间 |

---

## 3. 生成历史表 `history.xlsx`

记录每次香水生成请求和结果。

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | int | 自增ID |
| `session_id` | string | 会话唯一标识（UUID） |
| `user_text` | string | 用户原始输入 |
| `occasion` | string | 使用场合 |
| `city` | string | 查询天气的城市 |
| `mood` | string | 分析出的情绪倾向 |
| `scent_keywords` | string | 气味关键词（JSON 数组字符串） |
| `formula_name` | string | 生成的配方名称 |
| `matching_score` | float | 匹配度评分 |
| `created_at` | datetime | 生成时间 |

---

## 数据初始化

运行项目前，请在 `backend/database/data/` 下创建 `ingredients.xlsx`，
至少填入 10-20 种常见香水原料。可参考上方示例数据格式。

`formulas.xlsx` 和 `history.xlsx` 可以在运行后自动生成。
