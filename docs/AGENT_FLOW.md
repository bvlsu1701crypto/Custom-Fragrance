# Agent 工作流文档

## 整体架构

```
用户输入
   │
   ▼
┌─────────────────┐
│ InputProcessor  │  文字清洗 + 图片压缩
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WeatherAPI     │  查询天气（可选）
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│         Agent 1: Analyzer       │
│  输入：文字 + 图片 + 天气 + 场合  │
│  输出：结构化香水需求分析报告      │
└────────────────┬────────────────┘
                 │ AnalysisResult
                 ▼
┌─────────────────┐
│  DatabaseManager│  按关键词查询原料
└────────┬────────┘
         │ available_ingredients
         ▼
┌─────────────────────────────────┐
│         Agent 2: Executor       │
│  输入：分析报告 + 可用原料列表    │
│  输出：配方 + 推荐语 + 使用建议   │
└────────────────┬────────────────┘
                 │
                 ▼
            最终返回给用户
```

---

## Agent 1：分析器 (AnalyzerAgent)

**文件**: `backend/agents/agent1_analyzer.py`

### 输入
| 参数 | 类型 | 说明 |
|------|------|------|
| user_text | str | 清洗后的用户文字描述 |
| image_path | str? | 预处理后的图片路径 |
| weather_data | dict? | 天气信息字典 |
| occasion | str? | 使用场合 |

### Claude Prompt 策略
- 角色设定：专业香水顾问
- 要求以 JSON 格式返回，便于程序解析
- 提取维度：情绪倾向、季节、强度、气味关键词

### 输出：AnalysisResult
```python
AnalysisResult(
    mood="清新",
    season_fit="春",
    intensity="中",
    scent_keywords=["花香", "柑橘", "麝香"],
    occasion_type="约会",
    raw_analysis="用户希望一款清新..."
)
```

---

## Agent 2：执行器 (ExecutorAgent)

**文件**: `backend/agents/agent2_executor.py`

### 输入
| 参数 | 类型 | 说明 |
|------|------|------|
| analysis_result | AnalysisResult | Agent 1 的分析结果 |
| available_ingredients | list[dict] | 数据库查询出的可用原料 |

### Claude Prompt 策略
- 角色设定：专业调香师
- 将用户需求 + 可用原料表格传入
- 要求从原料库中选取，输出前/中/后调搭配及比例
- 生成香水故事和使用建议

### 输出：PerfumeRecommendation
```python
PerfumeRecommendation(
    formula=PerfumeFormula(
        name="春日漫步",
        top_notes=[...],
        middle_notes=[...],
        base_notes=[...],
    ),
    story="这款香水如同...",
    usage_tips="喷于手腕...",
    matching_score=92.5
)
```

---

## 编排器 (Orchestrator)

**文件**: `backend/services/orchestrator.py`

负责按顺序调用以上所有组件，处理异常，保证流程健壮。

### 执行顺序
1. `InputProcessor.process()` → 清洗输入
2. `WeatherAPIService.get_current_weather()` → 获取天气（可选）
3. `AnalyzerAgent.analyze()` → Agent 1 分析
4. `DatabaseManager.query_ingredients()` → 查询匹配原料
5. `ExecutorAgent.execute()` → Agent 2 生成配方
6. 返回 `PerfumeGenerationResult`
