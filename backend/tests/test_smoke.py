"""Tests minimaux sans connexion DB (import main déclenche create_all)."""


def test_settings_load():
    from app.core.config import settings

    assert settings.APP_NAME
