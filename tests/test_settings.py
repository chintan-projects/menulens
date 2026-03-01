"""Tests for application settings."""

from src.config.settings import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_defaults(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.discovery_default_radius_miles == 5
        assert settings.extraction_confidence_threshold == 0.8
        assert settings.extraction_model_primary == "lfm2-8b-a1b"

    def test_get_settings_returns_instance(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_llm_defaults(self) -> None:
        """LLM host, port, and model have sane defaults."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.llm_host == "localhost"
        assert settings.llm_port == 8081
        assert settings.extraction_model_primary == "lfm2-8b-a1b"
        assert settings.extraction_model_fallback == "claude-sonnet-4-20250514"

    def test_llm_base_url_computed_from_host_and_port(self) -> None:
        """llm_base_url property builds URL from host + port."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            llm_host="10.0.0.5",
            llm_port=9090,
        )
        assert settings.llm_base_url == "http://10.0.0.5:9090"

    def test_llm_base_url_default(self) -> None:
        """Default llm_base_url points at localhost:8081."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.llm_base_url == "http://localhost:8081"

    def test_anthropic_key_defaults_empty(self) -> None:
        """Anthropic API key defaults to empty (fallback disabled)."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.anthropic_api_key == ""

    def test_custom_llm_port_via_constructor(self) -> None:
        """LLM port can be overridden (simulating LLM_PORT env var)."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            llm_port=7777,
        )
        assert settings.llm_port == 7777
        assert settings.llm_base_url == "http://localhost:7777"
