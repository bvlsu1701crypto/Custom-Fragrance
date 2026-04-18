"""
应用入口 (Main Entry Point)

启动 FastAPI 应用，注册路由、中间件、启动事件
运行方式：
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from config.settings import get_settings
from database.db_manager import DatabaseManager


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时预加载数据库数据，关闭时做清理
    """
    # 启动：预加载 Excel 数据到内存
    print("[Startup] 加载香水原料数据库...")
    db = DatabaseManager(db_path=settings.DATABASE_PATH)
    db.load_data()
    app.state.db = db
    print("[Startup] 服务启动完成 ✓")

    yield  # 应用运行中

    # 关闭：清理资源
    print("[Shutdown] 服务关闭")


app = FastAPI(
    title="香水AI生成器 API",
    description="基于 Claude 双 Agent 架构的个性化香水配方生成服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)

# ── 跨域中间件（允许前端访问）─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册 API 路由 ──────────────────────────────
app.include_router(router)


@app.get("/")
async def root():
    """根路由，返回服务基本信息"""
    return {
        "service": "香水AI生成器",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
