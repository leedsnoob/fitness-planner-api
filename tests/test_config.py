from app.core.config import Settings


def test_settings_load_expected_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.app_name == "Fitness Planner API"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == "postgresql+psycopg://tomchen@localhost:5432/fitness_planner"


def test_settings_normalize_postgresql_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/fitness_planner")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/fitness_planner"


def test_settings_normalize_postgres_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@db.example.com:5432/fitness_planner")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/fitness_planner"
