# 后端项目追踪文件

本文档只记录当前 worktree `/Users/coy/.codex/worktrees/bc84/Custom-Fragrance` 的真实状态，用于推进黑客松项目的后端 demo。本文档本身不代表“理想架构”，只记录当前已经有的内容、已确认的阻塞项，以及下一步最小可执行动作。

## 1. 目标与范围

### 项目目标

做一个 AI 定制香水后端，围绕用户的当下状态和偏好生成可执行的香水方案。

当前产品目标输入包括：
- 用户文字描述
- 使用场合
- 天气 / 温度 / 湿度
- 体温或可穿戴设备数据
- 偏好香调
- 喜欢的现有香水

目标输出包括：
- 在限定原材料范围内生成的香水配方
- 原料配比
- 浓度建议
- 前调 / 中调 / 后调说明
- 气味描述
- 生成理由与推荐解释

### 当前范围

本文件以“后端 demo 落地”为主，只关心当前仓库能否尽快跑通最小链路。前端、赛道、长期数据库设计只在影响当前 demo 时提及。

## 2. 当前已有内容

### 后端服务骨架

- 已有 FastAPI 服务入口 [backend/main.py](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/backend/main.py)。
- 已有健康检查接口：`GET /api/health`
- 已有核心生成接口：`POST /api/generate`
- 已有原料列表接口：`GET /api/ingredients`
- 已有历史记录接口：`GET /api/history`

### 推荐生成主链路

- 已有双 Agent 骨架：
  - Agent 1：分析用户需求
  - Agent 2：基于候选原料生成香水配方
- 已有 Orchestrator 串联输入处理、天气服务、需求分析、原料查询和配方生成。
- 当前 Agent2 的真实工作方式是：
  - 吃 `available_ingredients` 列表
  - 把候选原料拼进 prompt
  - 交给 LLM 生成前调 / 中调 / 后调和比例
- 当前仓库里还没有把“30 个香基”作为结构化模板接进 Agent2 主流程。

### 数据层当前状态

- 当前 [backend/database/db_manager.py](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/backend/database/db_manager.py) 读取的是：
  - `ingredients.xlsx`
  - `formulas.xlsx`
  - `formula_details.xlsx`
  - `history.xlsx`
- 当前 [backend/database/data](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/backend/database/data) 目录只有 `.gitkeep`，运行时数据库文件尚未生成。
- 当前仓库里已有数据库 schema 文档和数据层代码，但还没有真实数据喂给运行时。

### 文档和资料

- 已有 API 文档 [docs/API.md](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/docs/API.md)。
- 已有 Agent 工作流文档 [docs/AGENT_FLOW.md](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/docs/AGENT_FLOW.md)。
- 已有数据库文档 [docs/DATABASE_SCHEMA.md](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/docs/DATABASE_SCHEMA.md)。
- 前端目前仍是占位状态，尚未开始真实联调。
- `30个香基规划.xlsx` 目前只算外部规划数据源，还没有接入当前运行时数据库。

## 3. 当前缺口 / 风险

### 已确认的 demo 阻塞项

- 运行时数据文件未生成。当前 `backend/database/data/` 为空，因此 `/api/ingredients` 现在无法返回真实数据，数据库层会落到空表。
- 当前数据层代码期望读取 `ingredients.xlsx / formulas.xlsx / formula_details.xlsx / history.xlsx`，但这几张表都还不存在。
- 根目录或外部的香基规划表尚未映射到当前 schema，因此“有规划表”不等于“后端已经可读”。
- 当前主流程没有把 30 个香基作为静态配方库接入推荐链路；它们目前只能算待接入的数据源，不是当前 Agent2 已消费的数据层。

### 工程与交付风险

- 当前无自动化测试。
- 当前无真实前端联调。
- 当前无端到端验收记录。
- 当前即使代码骨架存在，也还没有一次基于真实原料数据的完整运行结果。

## 4. 后端下一步（按优先级）

### P0 数据打通

- 确定最终采用的数据文件命名，并与当前 `db_manager.py` 的读取方式对齐。
- 把外部香基规划表映射为当前后端需要的运行时 `.xlsx`。
- 让 `backend/database/data/` 至少具备可读取的原料数据文件。
- 让 `GET /api/ingredients` 返回非空数据。

### P0 最小链路验收

- 跑通一次完整请求。
- 确认一次完整输出里前调 / 中调 / 后调都非空。
- 确认后端启动日志无 ERROR。

### P1 联调与展示

- 前端联调。
- 文案微调。
- 根据 demo 结果回看是否需要把 30 个香基接成静态模板层。

## 5. 阻塞项 / 待确认

- 最终要按当前代码的文件名产出数据，还是下一轮回改数据层读取路径。
- 30 个香基在 demo 里是只做静态展示素材，还是要接入推荐主流程。
- P0 阶段最小必需原料数是多少；当前目标建议至少满足 `/api/ingredients` 返回不少于 38 条。
- 体温 / wearable / 偏好香水这些增强输入，是 demo 首轮就接，还是等最小链路跑通后再加。

### 当前明确不做（demo 后再说）

- 本轮不改 [backend/database/db_manager.py](/Users/coy/.codex/worktrees/bc84/Custom-Fragrance/backend/database/db_manager.py)。
- 本轮不创建数据库文件，本文件只记录待办。
- 本轮不把持久化历史写入作为 demo blocker。
- 本轮不把更多 schema 扩展作为 demo blocker。
- 本轮不把构建脚本是否完善作为 demo blocker。

## 6. Demo Ready Checklist

三项全过即视为 demo ready：

| 项目 | 状态 | 备注 |
|------|------|------|
| 后端启动日志无 ERROR | 未开始 | 当前尚未基于真实数据验证 |
| `/api/ingredients` 返回不少于 38 条 | 未开始 | 当前数据目录为空 |
| 一次完整请求能拿到结果，且前 / 中 / 后调各至少 1 条 | 未开始 | 当前尚未完成端到端验证 |

## 7. 更新记录

- 2026-04-18：修订追踪文件，按当前 worktree 真实状态重写内容，删除不符合现状的理想化描述。明确本轮只更新 tracker，不改代码、不建数据文件。下一步优先处理运行时数据文件命名和 Excel 映射，再验证 `/api/ingredients` 与完整请求链路。
