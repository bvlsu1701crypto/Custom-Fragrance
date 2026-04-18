"""
API 路由与应用入口 (Routes)

包含：
  - FastAPI app 实例（含 CORS、全局异常处理）
  - POST /api/generate-perfume   核心生成接口
  - GET  /api/health             健康检查
  - GET  /api/debug/database-info 数据库统计（仅 DEBUG 模式）
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from database.db_manager import DatabaseManager
from database.schemas import Agent1Input, FinalOutput
from services.orchestrator import OrchestrationResult, PerfumeOrchestrator

logger = logging.getLogger(__name__)

# ── FastAPI 应用实例 ────────────────────────────────────────────

app = FastAPI(
    title="Custom Fragrance API",
    description="基于双 Agent（智谱 AI GLM）的个性化香水配方生成服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS 中间件 ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局请求日志中间件 ──────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录每个请求的方法、路径和耗时"""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "%s %s → %d (%.0fms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response

# ── 全局异常处理 ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的异常，返回统一 JSON 格式"""
    logger.error(
        "未处理异常 [%s %s]: %s",
        request.method, request.url.path, exc, exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务内部错误，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

# ── 懒加载单例（避免启动时若未配置 API Key 就崩溃）──────────────

_orchestrator: PerfumeOrchestrator | None = None

def _get_orchestrator() -> PerfumeOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PerfumeOrchestrator()
    return _orchestrator

# ──────────────────────────────────────────────────────────────
# 端点定义
# ──────────────────────────────────────────────────────────────

@app.post(
    "/api/generate-perfume",
    response_model=FinalOutput,
    summary="生成个性化香水配方",
    description=(
        "接收 Apple Watch 生理数据 + 问卷回答 + 天气信息，"
        "经双 Agent 分析后返回完整香水配方和描述文案。"
    ),
)
async def generate_perfume(body: Agent1Input) -> FinalOutput:
    """
    核心生成接口

    - Agent1 负责分析偏好画像和环境上下文
    - Agent2 负责选油、配比、生成描述文案
    - 若 weather.city == '未知'，服务端会根据经纬度自动查询天气
    """
    orchestrator = _get_orchestrator()

    result: OrchestrationResult = orchestrator.process_request(body)

    if not result.success:
        logger.warning(
            "[Route] /api/generate-perfume 生成失败：%s", result.error_message
        )
        raise HTTPException(status_code=500, detail=result.error_message)

    logger.info(
        "[Route] /api/generate-perfume 成功 | 耗时=%.2fs agent1=%.0fms agent2=%.0fms",
        result.duration_seconds,
        result.stage_timings.get("agent1_ms", 0),
        result.stage_timings.get("agent2_ms", 0),
    )
    return result.final_output


@app.get(
    "/api/health",
    summary="健康检查",
    response_description="服务状态信息",
)
async def health_check():
    """
    健康检查接口，可用于负载均衡器探活
    返回服务状态、版本和数据库加载情况
    """
    db = DatabaseManager.get_instance(settings.DATABASE_PATH)

    # 统计各表已加载条数
    formula_count = len(db._get("perfume_formula_database"))
    social_count  = len(db._get("social_distance_data"))
    oils_count    = len(db._get("essential_oils_diffusion_comparison"))
    db_ready      = formula_count > 0

    return {
        "success": True,
        "status": "ok" if db_ready else "degraded",
        "version": "1.0.0",
        "debug_mode": settings.DEBUG,
        "database": {
            "ready": db_ready,
            "perfume_formula_count": formula_count,
            "social_distance_count": social_count,
            "oils_diffusion_count":  oils_count,
        },
    }


@app.get(
    "/api/debug/database-info",
    summary="数据库统计（仅 DEBUG 模式）",
    include_in_schema=False,   # Swagger 中隐藏此端点
)
async def database_info():
    """
    返回数据库各表的详细统计信息
    仅在 settings.DEBUG=True 时可用，生产环境返回 403
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="该端点仅在 DEBUG 模式下可用",
        )

    db = DatabaseManager.get_instance(settings.DATABASE_PATH)

    def _table_summary(name: str) -> dict:
        records = db._get(name)
        if not records:
            return {"count": 0, "columns": [], "sample": []}
        columns = list(records[0].keys())
        return {
            "count": len(records),
            "columns": columns,
            # 最多返回前3条样本
            "sample": records[:3],
        }

    return {
        "success": True,
        "data_dir": settings.DATABASE_PATH,
        "tables": {
            "perfume_formula_database":            _table_summary("perfume_formula_database"),
            "social_distance_data":                _table_summary("social_distance_data"),
            "essential_oils_diffusion_comparison": _table_summary("essential_oils_diffusion_comparison"),
        },
    }
