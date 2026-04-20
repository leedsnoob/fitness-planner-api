import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import Base, get_engine, reset_db_state
from app.main import create_app


@pytest.fixture()
def reset_database() -> Generator[None, None, None]:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://tomchen@localhost:5432/fitness_planner_test"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars"
    get_settings.cache_clear()
    reset_db_state()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
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
