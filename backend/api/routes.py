"""
API 路由 (API Routes)

职责：
  - 创建 FastAPI app 并配置 CORS
  - 暴露两个核心端点：
      GET  /api/health            健康检查
      POST /api/generate-perfume  生成香水配方（Agent1 → Agent2）
  - 附带 /api/ingredients、/api/bases 查询接口
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.agent1_analyzer import Agent1Analyzer
from agents.agent2_executor import Agent2Executor
from config.settings import settings
from database.db_manager import DatabaseManager
from database.schemas import Agent1Input, FinalOutput

logger = logging.getLogger(__name__)


# ── FastAPI app 初始化 ──────────────────────────────────────────

app = FastAPI(
    title="Custom Fragrance API",
    description="基于 Apple Watch 生理数据 + 问卷 + 天气的双 Agent 香水生成服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 健康检查 ────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """
    检查服务与 DB 状态。
    DB 可用 → status=ok，DB 加载异常 → status=degraded
    """
    try:
        db = DatabaseManager.get_instance(settings.DATABASE_PATH)
        ingredients_count = len(db.get_all_ingredients())
        bases_count       = len(db.get_all_bases())
        status = "ok" if ingredients_count > 0 and bases_count > 0 else "degraded"
        return {
            "status": status,
            "message": "服务运行中",
            "ingredients": ingredients_count,
            "bases": bases_count,
        }
    except Exception as exc:
        logger.exception("[Health] 检查失败")
        return {"status": "degraded", "message": f"DB 异常: {exc}"}


# ── 核心接口：生成香水配方 ──────────────────────────────────────

@app.post("/api/generate-perfume", response_model=FinalOutput)
async def generate_perfume(request: Agent1Input):
    """
    完整生成流程：
      1. Agent1Analyzer 综合生理/环境/问卷 → 偏好画像
      2. Agent2Executor 在已加载的数据库中筛选精油、计算配比、生成文案
      3. 返回 FinalOutput（配方 + 描述 + 规格参数）
    """
    try:
        logger.info(
            "[API] 收到生成请求 | 场合=%s 城市=%s",
            request.questionnaire.occasion,
            request.weather.city,
        )

        analyzer = Agent1Analyzer()
        analysis = analyzer.analyze(request)

        executor = Agent2Executor()
        result   = executor.execute(analysis, language=request.language)

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[API] 生成失败")
        raise HTTPException(status_code=500, detail=f"生成失败: {exc}")


# ── 辅助接口：原料 / 香基查询 ───────────────────────────────────

@app.get("/api/ingredients")
async def list_ingredients():
    db = DatabaseManager.get_instance(settings.DATABASE_PATH)
    ingredients = db.get_all_ingredients()
    return {"ingredients": ingredients, "total": len(ingredients)}


@app.get("/api/bases")
async def list_bases():
    db = DatabaseManager.get_instance(settings.DATABASE_PATH)
    bases = db.get_all_bases()
    return {"bases": bases, "total": len(bases)}


@app.get("/api/bases/{base_id}")
async def get_base_detail(base_id: str):
    db = DatabaseManager.get_instance(settings.DATABASE_PATH)
    base = db.get_base_with_details(base_id)
    if base is None:
        raise HTTPException(status_code=404, detail=f"香基 {base_id} 不存在")
    return base
