# Custom Fragrance AI Generator

个性化香水AI生成器 — 基于 Claude 双 Agent 架构

## 分支说明

| 分支 | 内容 | 说明 |
|------|------|------|
| [`backend`](../../tree/backend) | 后端服务 | FastAPI + Claude Agent，香水配方生成逻辑 |
| [`frontend`](../../tree/frontend) | 前端界面 | 用户交互界面（开发中） |

## 快速开始

**后端开发：**
```bash
git checkout backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**前端开发：**
```bash
git checkout frontend
cd frontend
```
