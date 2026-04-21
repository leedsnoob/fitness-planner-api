from __future__ import annotations

import os
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url

from app.core.config import get_settings
from app.db.session import reset_db_state


DEFAULT_BASE_DATABASE_URL = "postgresql+psycopg://tomchen@localhost:5432/fitness_planner_test"


def _build_admin_url(database_url: str) -> URL:
    return make_url(database_url).set(database="postgres")


def _database_name(database_url: str) -> str:
    return make_url(database_url).database or "fitness_planner_test"


def _create_database(database_url: str) -> None:
    database_name = _database_name(database_url)
    admin_engine = create_engine(_build_admin_url(database_url), isolation_level="AUTOCOMMIT", future=True)
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :database_name AND pid <> pg_backend_pid()"
            ),
            {"database_name": database_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    admin_engine.dispose()


def _drop_database(database_url: str) -> None:
    database_name = _database_name(database_url)
    admin_engine = create_engine(_build_admin_url(database_url), isolation_level="AUTOCOMMIT", future=True)
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :database_name AND pid <> pg_backend_pid()"
            ),
            {"database_name": database_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
    admin_engine.dispose()


def test_alembic_upgrade_creates_current_schema() -> None:
    base_url = make_url(os.environ.get("TEST_DATABASE_URL", DEFAULT_BASE_DATABASE_URL))
    database_url = str(base_url.set(database=f"fitness_planner_migration_{uuid4().hex[:8]}"))
    _create_database(database_url)
    previous_database_url = os.environ.get("DATABASE_URL")

    try:
        os.environ["DATABASE_URL"] = database_url
        get_settings.cache_clear()
        reset_db_state()

        config = Config("alembic.ini")
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        table_names = set(inspect(engine).get_table_names())
        engine.dispose()

        assert table_names == {
            "adjustment_requests",
            "alembic_version",
            "exercises",
            "plan_explanations",
            "plan_revisions",
            "training_plans",
            "user_profiles",
            "users",
            "workout_logs",
            "workout_session_exercises",
            "workout_sessions",
        }
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        get_settings.cache_clear()
        reset_db_state()
        _drop_database(database_url)
