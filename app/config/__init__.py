"""Configuration module for prompts, models and app settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    site_url: str = Field(default="http://localhost:8000", alias="SITE_URL")
    llm_model: str = Field(default="x-ai/grok-beta-fast", alias="LLM_MODEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance with validation
try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Failed to load settings. Please check your .env file exists and contains "
        f"required variables: TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY. "
        f"You can copy .env.example to .env and fill in your values. Error: {e}"
    )


__all__ = ["settings", "Settings"]


