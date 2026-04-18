"""
配置文件 (Settings)

从环境变量或 .env 文件读取配置，导出 settings 单例供其他模块使用。

使用方式：
  from config.settings import settings
  print(settings.ANTHROPIC_API_KEY)
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置类
    字段优先从环境变量读取，其次使用默认值
    """

    # ── 必需：Anthropic API Key ────────────────
    ANTHROPIC_API_KEY: str

    # ── 数据库配置 ─────────────────────────────
    DATABASE_PATH: str = "database/data"

    # ── 服务器配置 ─────────────────────────────
    PORT: int = 8000
    DEBUG: bool = True

    # ── CORS 配置 ──────────────────────────────
    # 从环境变量读取逗号分隔的字符串，自动解析为列表
    # 例：ALLOWED_ORIGINS=http://localhost:3000,https://*.vercel.app
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "ANTHROPIC_API_KEY 不能为空，请在 .env 文件中配置有效的 API Key"
            )
        return v.strip()

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """支持逗号分隔字符串和列表两种格式"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# 全局单例，直接导入使用
settings = Settings()
