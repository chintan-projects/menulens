"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_models_dir() -> str:
    """Resolve default MODELS_DIR to ~/Projects/_models."""
    return str(Path.home() / "Projects" / "_models")


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

    # Model registry — shared across all projects (see ~/Projects/_models/config.yaml).
    # Override with MODELS_DIR env var to point at a different location.
    models_dir: str = _default_models_dir()

    # LLM - Primary (llama-server with OpenAI-compatible API)
    llm_host: str = "localhost"
    llm_port: int = 8081
    extraction_model_primary: str = "lfm2-8b-a1b"

    @property
    def llm_base_url(self) -> str:
        """Computed base URL from host and port."""
        return f"http://{self.llm_host}:{self.llm_port}"

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
