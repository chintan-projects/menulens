"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MenuLens application configuration.

    All values loaded from environment variables or .env file.
    No hardcoded defaults for secrets or external service URLs.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://menulens:menulens@localhost:5432/menulens"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google Maps
    google_maps_api_key: str = ""

    # LLM - Primary (ollama local)
    ollama_base_url: str = "http://localhost:11434"
    extraction_model_primary: str = "lfm2-8b-a1b"

    # LLM - Fallback (Claude API)
    anthropic_api_key: str = ""
    extraction_model_fallback: str = "claude-sonnet-4-20250514"

    # Extraction
    extraction_confidence_threshold: float = 0.8

    # Discovery
    discovery_default_radius_miles: int = 5
    discovery_max_results: int = 200

    # Storage
    raw_content_dir: str = "data/raw"
    extracted_content_dir: str = "data/extracted"


def get_settings() -> Settings:
    """Create and return application settings instance."""
    return Settings()
