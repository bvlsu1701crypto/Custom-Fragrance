# Custom Fragrance AI Generator

个性化香水 AI 生成器，当前 `main` 分支用于展示前端与后端合并后的完整仓库内容。

## 目录结构

```text
.
├── frontend/   # Next.js 前端界面
├── backend/    # FastAPI 后端服务
├── docs/       # 接口与架构文档
├── render.yaml # Render 部署配置
└── README.md
```

## 分支说明

| 分支 | 内容 | 说明 |
|------|------|------|
| [`main`](../../tree/main) | 合并视图 | 同时包含前端与后端，便于统一查看完整项目 |
| [`frontend`](../../tree/frontend) | 前端界面 | 用户交互界面 |
| [`backend`](../../tree/backend) | 后端服务 | FastAPI + Claude Agent，香水配方生成逻辑 |

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 文档入口

- `docs/API.md`
- `docs/AGENT_FLOW.md`
- `docs/DATABASE_SCHEMA.md`
