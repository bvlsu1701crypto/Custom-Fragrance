"""
API 路由定义 (API Routes)

职责：
  - 定义所有 HTTP API 端点（FastAPI Router）
  - 处理请求参数解析、文件上传
  - 调用 Orchestrator 执行业务逻辑
  - 格式化并返回标准化响应

API 端点一览（详见 docs/API.md）：
  POST /api/generate          生成香水配方（核心接口）
  GET  /api/ingredients       获取原料列表
  GET  /api/history           获取生成历史
  GET  /api/health            健康检查
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import shutil
import os
import uuid

from api.models import (
    GenerateRequest,
    GenerateResponse,
    IngredientsResponse,
    HealthResponse,
)
from services.orchestrator import Orchestrator, PerfumeGenerationRequest
from config.settings import get_settings

router = APIRouter(prefix="/api", tags=["perfume"])

# 临时文件上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    用于监控服务是否正常运行
    """
    return HealthResponse(status="ok", message="香水AI生成器服务运行正常")


@router.post("/generate", response_model=GenerateResponse)
async def generate_perfume(
    user_text: str = Form(..., description="用户对香水的文字描述"),
    occasion: Optional[str] = Form(None, description="使用场合"),
    city: Optional[str] = Form(None, description="城市名（用于天气查询）"),
    image: Optional[UploadFile] = File(None, description="可选的参考图片"),
    settings=Depends(get_settings),
):
    """
    香水生成核心接口

    接收用户的文字描述、场合、城市和可选图片，
    经过双 Agent 处理后返回个性化香水配方和推荐说明。
    """
    image_path = None

    # 保存上传的图片到临时目录
    if image:
        ext = os.path.splitext(image.filename)[1]
        temp_filename = f"{uuid.uuid4()}{ext}"
        image_path = os.path.join(UPLOAD_DIR, temp_filename)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

    try:
        orchestrator = Orchestrator(settings=settings)
        request = PerfumeGenerationRequest(
            user_text=user_text,
            image_path=image_path,
            occasion=occasion,
            city=city,
        )

        result = await orchestrator.generate_perfume(request)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        return GenerateResponse.from_result(result)

    finally:
        # 清理临时图片文件
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


@router.get("/ingredients", response_model=IngredientsResponse)
async def get_ingredients(settings=Depends(get_settings)):
    """
    获取全部可用原料列表
    前端可用于展示原料库或允许用户手动选择原料
    """
    from database.db_manager import DatabaseManager
    db = DatabaseManager(db_path=settings.DATABASE_PATH)
    ingredients = db.get_all_ingredients()
    return IngredientsResponse(ingredients=ingredients, total=len(ingredients))


@router.get("/history")
async def get_history(
    limit: int = 20,
    settings=Depends(get_settings),
):
    """
    获取香水生成历史记录
    返回最近 N 条生成记录
    """
    import pandas as pd
    history_path = os.path.join(settings.DATABASE_PATH, "history.xlsx")

    if not os.path.exists(history_path):
        return JSONResponse(content={"history": [], "total": 0})

    df = pd.read_excel(history_path)
    records = df.tail(limit).to_dict(orient="records")
    return JSONResponse(content={"history": records, "total": len(df)})
