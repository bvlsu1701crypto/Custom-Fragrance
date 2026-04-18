"""
配置文件 (Settings)

职责：
  - 集中管理所有配置项（API Key、路径、参数等）
  - 支持从环境变量或 .env 文件读取敏感配置
  - 提供全局单例 settings 对象供各模块引用
  - 区分开发环境和生产环境的配置

使用方式：
  from config.settings import get_settings
  settings = get_settings()
  print(settings.ANTHROPIC_API_KEY)

环境变量配置（创建 backend/.env 文件）：
  ANTHROPIC_API_KEY=sk-ant-...
  WEATHER_API_KEY=your_openweathermap_key
  DATABASE_PATH=./database/data
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    全局配置类
    字段优先从环境变量读取，其次使用默认值
    """

    # ── API Keys ──────────────────────────────
    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="Anthropic Claude API Key，从 https://console.anthropic.com 获取",
    )
    WEATHER_API_KEY: str = Field(
        default="",
        description="OpenWeatherMap API Key，用于获取天气数据",
    )

    # ── 数据库配置 ─────────────────────────────
    DATABASE_PATH: str = Field(
        default="./database/data",
        description="Excel 数据文件所在目录路径",
    )

    # ── 服务器配置 ─────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8000, description="服务监听端口")
    DEBUG: bool = Field(default=True, description="是否开启调试模式")

    # ── Claude 模型配置 ────────────────────────
    CLAUDE_MODEL: str = Field(
        default="claude-opus-4-6",
        description="使用的 Claude 模型版本",
    )
    MAX_TOKENS: int = Field(default=2048, description="Claude 最大返回 token 数")

    # ── 文件上传配置 ───────────────────────────
    UPLOAD_DIR: str = Field(default="./uploads", description="临时文件上传目录")
    MAX_IMAGE_SIZE_MB: float = Field(default=5.0, description="图片上传最大大小（MB）")

    # ── CORS 配置（跨域）─────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许跨域的前端地址列表",
    )

    class Config:
        # 从 backend/.env 文件读取配置
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取全局配置单例（使用 lru_cache 保证只初始化一次）
    FastAPI Depends 注入时调用此函数
    """
    return Settings()
