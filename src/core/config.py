"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "radar_user"
    postgres_password: str = "radar_password"
    postgres_db: str = "radar_db"

    # ClickHouse Configuration
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_db: str = "radar_clickhouse"

    # RabbitMQ Configuration
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "radar_user"
    rabbitmq_password: str = "radar_password"
    rabbitmq_vhost: str = "/"

    # LLM Configuration
    openrouter_api_key: str = "your_api_key_here"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Application Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Faiss Configuration
    faiss_index_path: str = "./data/faiss_index"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dedup_similarity_threshold: float = 0.85

    # News Processing Configuration
    news_queue_name: str = "news_ingestion_queue"
    prefetch_count: int = 10
    
    # Parser Configuration
    parser_interval_minutes: int = 5
    fasttext_min_score: float = 0.5  # Minimum confidence for FastText classification

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        """Generate RabbitMQ connection URL"""
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

