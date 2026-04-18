# 香水AI生成器

基于 Claude 双 Agent 架构的个性化香水配方生成系统。用户输入文字描述、参考图片和使用场合，系统自动分析需求并生成专属香水配方。

## 项目结构

```
Hackathon1819/
├── frontend/               # 前端（待开发）
│   └── README.md
├── backend/                # 后端服务
│   ├── agents/             # 智能体模块
│   │   ├── agent1_analyzer.py    # Agent 1：分析用户需求
│   │   └── agent2_executor.py    # Agent 2：生成香水配方
│   ├── services/           # 业务逻辑层
│   │   ├── orchestrator.py       # 流程编排器（总调度）
│   │   ├── input_processor.py    # 用户输入预处理
│   │   └── weather_api.py        # 天气 API 服务
│   ├── database/           # 数据层
│   │   ├── data/                 # Excel 数据文件目录
│   │   ├── db_manager.py         # 数据库操作管理器
│   │   └── schemas.py            # 数据表字段定义
│   ├── api/                # API 接口层
│   │   ├── routes.py             # FastAPI 路由定义
│   │   └── models.py             # 请求/响应数据模型
│   ├── config/             # 配置
│   │   └── settings.py           # 全局配置（环境变量）
│   ├── main.py             # 应用入口
│   └── requirements.txt    # Python 依赖
├── docs/                   # 文档
│   ├── API.md              # API 接口文档
│   ├── AGENT_FLOW.md       # Agent 工作流说明
│   └── DATABASE_SCHEMA.md  # 数据库结构说明
└── README.md               # 本文件
```

## 技术架构

```
用户请求
   ↓
FastAPI (api/routes.py)
   ↓
Orchestrator (services/orchestrator.py)
   ↓              ↓
Agent 1        WeatherAPI
(分析需求)     (天气查询)
   ↓
DatabaseManager
(查询匹配原料)
   ↓
Agent 2
(生成配方)
   ↓
返回结果
```

### 核心技术
- **后端框架**: FastAPI + Uvicorn
- **AI 模型**: Claude claude-opus-4-6（双 Agent）
- **数据存储**: Excel（Pandas + openpyxl）
- **图片处理**: Pillow

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
WEATHER_API_KEY=your-openweathermap-key  # 可选
DATABASE_PATH=./database/data
```

### 3. 准备数据

在 `backend/database/data/` 目录下创建 `ingredients.xlsx`，
参考 `docs/DATABASE_SCHEMA.md` 填入香水原料数据。

### 4. 启动服务

```bash
cd backend
uvicorn main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

## API 使用示例

```bash
curl -X POST http://localhost:8000/api/generate \
  -F "user_text=我想要一款适合春天约会的清新花香调香水" \
  -F "occasion=约会" \
  -F "city=上海"
```

详细 API 文档见 [docs/API.md](docs/API.md)。

## 文档索引

| 文档 | 说明 |
|------|------|
| [docs/API.md](docs/API.md) | 完整 API 接口文档 |
| [docs/AGENT_FLOW.md](docs/AGENT_FLOW.md) | Agent 工作流和架构说明 |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | 数据库表结构说明 |
