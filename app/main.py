from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.me import router as me_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.app_env,
        }

    app.include_router(auth_router)
    app.include_router(me_router)

    return app


app = create_app()
