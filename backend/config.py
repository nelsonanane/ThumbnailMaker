"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Thumbnail Generator API"
    debug: bool = False
    api_version: str = "v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # AI Services
    fal_key: str = ""
    openai_api_key: str = ""
    google_ai_api_key: str = ""

    # Image Generator Selection (flux or imagen)
    image_generator_backend: str = "imagen"

    # YouTube
    youtube_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379"

    # Generation defaults
    default_num_images: int = 4
    default_image_size: str = "landscape_16_9"
    flux_guidance_scale: float = 3.5
    flux_inference_steps: int = 28

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()

# Set API keys in environment for clients to pick up
if settings.fal_key:
    os.environ["FAL_KEY"] = settings.fal_key
if settings.google_ai_api_key:
    os.environ["GOOGLE_AI_API_KEY"] = settings.google_ai_api_key
