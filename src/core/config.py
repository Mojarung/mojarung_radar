from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="RADAR", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")

    redis_url: RedisDsn = Field(alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")

    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")

    hotness_threshold: float = Field(default=0.7, alias="HOTNESS_THRESHOLD")
    dedup_similarity_threshold: float = Field(default=0.85, alias="DEDUP_SIMILARITY_THRESHOLD")
    top_k_stories: int = Field(default=10, alias="TOP_K_STORIES")

    news_sources: str = Field(default="bloomberg,reuters", alias="NEWS_SOURCES")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    @field_validator("news_sources", mode="before")
    @classmethod
    def parse_news_sources(cls, v: str | list[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def news_sources_list(self) -> list[str]:
        return [s.strip() for s in self.news_sources.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

