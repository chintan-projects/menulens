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
