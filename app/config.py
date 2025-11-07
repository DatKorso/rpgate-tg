"""
Configuration module для загрузки environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    site_url: str = Field(default="http://localhost:8000", alias="SITE_URL")
    llm_model: str = Field(default="x-ai/grok-4-fast", alias="LLM_MODEL")
    
    # Supabase Configuration (Sprint 3)
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    supabase_db_url: Optional[str] = Field(default=None, alias="SUPABASE_DB_URL")
    
    # OpenAI Configuration (for embeddings)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton instance с валидацией
try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Failed to load settings. Please check your .env file exists and contains "
        f"required variables: TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY. "
        f"You can copy .env.example to .env and fill in your values. Error: {e}"
    )
