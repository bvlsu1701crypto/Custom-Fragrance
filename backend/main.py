"""
应用入口 (Main Entry Point)

启动方式：
  python main.py
  或
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import logging.config

import uvicorn

from config.settings import settings

# ── 日志配置 ────────────────────────────────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "DEBUG" if settings.DEBUG else "INFO",
        "handlers": ["console"],
    },
    # 降低第三方库的日志级别，避免刷屏
    "loggers": {
        "uvicorn":        {"level": "INFO",    "propagate": True},
        "uvicorn.access": {"level": "WARNING", "propagate": True},
        "httpx":          {"level": "WARNING", "propagate": True},
        "openai":         {"level": "WARNING", "propagate": True},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ── 导入 FastAPI app（日志初始化后再导入，确保模块内 logger 生效）──

from api.routes import app  # noqa: E402


# ── 启动入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  Custom Fragrance API  启动中...")
    logger.info("=" * 60)
    logger.info("  端口     : %d", settings.PORT)
    logger.info("  调试模式 : %s", settings.DEBUG)
    logger.info("  数据目录 : %s", settings.DATABASE_PATH)
    logger.info("  CORS 源  : %s", settings.ALLOWED_ORIGINS)
    logger.info("  文档地址 : http://localhost:%d/docs", settings.PORT)
    logger.info("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,    # 使用上方自定义日志配置，禁用 uvicorn 默认配置
    )
