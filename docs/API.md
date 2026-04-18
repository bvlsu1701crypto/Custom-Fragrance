# API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 前缀**: `/api`
- **文档 UI**: `http://localhost:8000/docs`（Swagger）

---

## 接口列表

### 1. 生成香水配方

**`POST /api/generate`**

核心接口，接收用户描述，返回个性化香水配方。

**请求格式**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_text` | string | ✅ | 用户对香水的文字描述（2-500字） |
| `occasion` | string | ❌ | 使用场合（约会/工作/休闲/运动等） |
| `city` | string | ❌ | 城市名，用于查询天气（如：上海） |
| `image` | file | ❌ | 参考图片（jpg/png/webp，最大5MB） |

**响应示例**:
```json
{
  "success": true,
  "formula": {
    "name": "春日漫步",
    "description": "清新的花果调，带来春天的愉悦感受",
    "top_notes": [
      {"name": "Bergamot", "name_cn": "佛手柑", "category": "前调", "scent_type": "柑橘", "intensity_level": 3, "ratio": 0.3}
    ],
    "middle_notes": [
      {"name": "Rose", "name_cn": "玫瑰", "category": "中调", "scent_type": "花香", "intensity_level": 3, "ratio": 0.4}
    ],
    "base_notes": [
      {"name": "Musk", "name_cn": "麝香", "category": "后调", "scent_type": "麝香", "intensity_level": 2, "ratio": 0.3}
    ],
    "total_volume_ml": 10
  },
  "story": "这款香水如同春日清晨漫步在玫瑰园，清新的佛手柑前调带来愉悦，玫瑰中调诉说浪漫，温柔的麝香余香持久萦绕。",
  "usage_tips": "喷于手腕和颈部，约会场合尤为适合。",
  "matching_score": 92.5,
  "analysis_summary": {
    "mood": "清新",
    "season_fit": "春",
    "intensity": "中",
    "scent_keywords": ["花香", "柑橘", "麝香"],
    "occasion_type": "约会"
  },
  "weather_info": {
    "temperature": 22.5,
    "humidity": 60,
    "condition": "晴天",
    "city": "上海",
    "season": "春",
    "temp_level": "温暖",
    "humidity_level": "适中"
  }
}
```

---

### 2. 获取原料列表

**`GET /api/ingredients`**

返回全部可用香水原料。

**响应示例**:
```json
{
  "ingredients": [
    {
      "id": 1,
      "name": "Bergamot",
      "name_cn": "佛手柑",
      "category": "前调",
      "scent_type": "柑橘",
      "intensity_level": 3,
      "season_fit": "春夏"
    }
  ],
  "total": 50
}
```

---

### 3. 获取生成历史

**`GET /api/history?limit=20`**

返回最近 N 条生成记录。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | int | 20 | 返回记录数量 |

---

### 4. 健康检查

**`GET /api/health`**

```json
{
  "status": "ok",
  "message": "香水AI生成器服务运行正常"
}
```

---

## 错误响应

```json
{
  "detail": "错误描述信息"
}
```

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 请求参数错误 |
| 422 | 参数校验失败 |
| 500 | 服务内部错误 |
