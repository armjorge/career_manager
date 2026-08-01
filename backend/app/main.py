from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_db_connection
from app.routers import analytics, applications, companies, documents, health, me, sites


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Career Manager API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "prod" else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "message" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"message": "Invalid request payload", "code": "VALIDATION_ERROR"},
        )

    @app.get(f"{settings.api_prefix}/health")
    def api_health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get(f"{settings.api_prefix}/health/db")
    def api_health_db() -> dict[str, str]:
        if not settings.db_postgresql:
            raise HTTPException(
                status_code=503,
                detail={"message": "DB_POSTGRESQL is not configured", "code": "DB_UNAVAILABLE"},
            )
        check_db_connection()
        return {"status": "healthy", "database": "connected"}

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(companies.router, prefix=settings.api_prefix)
    app.include_router(applications.router, prefix=settings.api_prefix)
    app.include_router(analytics.router, prefix=settings.api_prefix)
    app.include_router(documents.router, prefix=settings.api_prefix)
    app.include_router(sites.router, prefix=settings.api_prefix)

    return app


app = create_app()
