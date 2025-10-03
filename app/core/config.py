from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    database_url: str
    redis_url: str
    openrouter_api_key: str
    log_level: str = "INFO"
    
    api_v1_prefix: str = "/api/v1"
    project_name: str = "RADAR - Hot News Detector"
    
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_llm_model: str = "anthropic/claude-3.5-sonnet"
    
    hotness_threshold: float = 0.7
    top_k_stories: int = 10
    dedup_threshold: float = 0.85


settings = Settings()

