from fastapi import FastAPI

from realestate_rag_agent.api.health import router as health_router
from realestate_rag_agent.api.properties import router as properties_router
from realestate_rag_agent.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug,
    )
    app.include_router(health_router)
    app.include_router(properties_router)
    return app


app = create_app()
