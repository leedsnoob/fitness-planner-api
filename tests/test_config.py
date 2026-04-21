from app.core.config import Settings


def test_settings_load_expected_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.app_name == "Fitness Planner API"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == "postgresql+psycopg://tomchen@localhost:5432/fitness_planner"
    assert settings.siliconflow_connect_timeout_seconds == 5.0
    assert settings.siliconflow_read_timeout_seconds == 60.0


def test_settings_normalize_postgresql_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/fitness_planner")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/fitness_planner"


def test_settings_normalize_postgres_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@db.example.com:5432/fitness_planner")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/fitness_planner"


def test_settings_allow_timeout_override(monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_READ_TIMEOUT_SECONDS", "75")

    settings = Settings(_env_file=None)

    assert settings.siliconflow_read_timeout_seconds == 75.0
