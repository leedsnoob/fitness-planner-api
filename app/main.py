from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.exercises import custom_router as custom_exercises_router
from app.api.routes.exercises import router as exercises_router
from app.api.routes.me import router as me_router
from app.core.config import get_settings
from app.db.session import get_session_factory


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.session_factory = get_session_factory()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.app_env,
        }

    app.include_router(auth_router)
    app.include_router(exercises_router)
    app.include_router(me_router)
    app.include_router(custom_exercises_router)

    return app


app = create_app()
