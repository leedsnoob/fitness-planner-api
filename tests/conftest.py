import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app.core.config import get_settings
from app.db.session import Base, get_engine, reset_db_state
from app.main import create_app


DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://tomchen@localhost:5432/fitness_planner_test"


def _build_worker_database_url() -> str:
    base_url = make_url(os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL))
    base_name = base_url.database or "fitness_planner_test"
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "local")
    pid = os.getpid()
    database_name = f"{base_name}_{worker_id}_{pid}"
    return str(base_url.set(database=database_name))


def _build_admin_url(database_url: str) -> URL:
    return make_url(database_url).set(database="postgres")


def _database_name(database_url: str) -> str:
    return make_url(database_url).database or "fitness_planner_test"


def _recreate_database(database_url: str) -> None:
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


@pytest.fixture(scope="session")
def worker_database_url() -> Generator[str, None, None]:
    database_url = _build_worker_database_url()
    _recreate_database(database_url)
    yield database_url
    _drop_database(database_url)


@pytest.fixture()
def reset_database(worker_database_url: str) -> Generator[None, None, None]:
    os.environ["DATABASE_URL"] = worker_database_url
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars"
    get_settings.cache_clear()
    reset_db_state()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    reset_db_state()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("JWT_SECRET_KEY", None)
    get_settings.cache_clear()
    reset_db_state()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def db_client(reset_database: None) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
