"""应用配置：pydantic-settings 从 .env / 环境变量读取。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    DB_DSN: str = "sqlite+aiosqlite:///./data/zhistack.db"
    STORAGE_ROOT: str = "./data/storage"
    CORS_ORIGINS: str = "http://localhost:5173"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # 模型（OpenAI 兼容协议，M4 起用；LLM_API_KEY 为空时走降级）
    LLM_DEFAULT_PROVIDER: str = "siliconflow"
    LLM_BASE_URL: str = "https://api.siliconflow.cn/v1"
    LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    LLM_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "dashscope"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIM: int = 1536

    # 限制
    MAX_UPLOAD_MB: int = 500
    AI_MONTHLY_BUDGET_USD: float = 20.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
