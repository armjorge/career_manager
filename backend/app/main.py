from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from backend.app.config import get_settings
from backend.app.database import check_db_connection
from backend.app.routers import applications, companies


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Career Manager API", version="0.1.0")

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
    def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get(f"{settings.api_prefix}/health/db")
    def health_db() -> dict[str, str]:
        check_db_connection()
        return {"status": "healthy", "database": "connected"}

    app.include_router(companies.router, prefix=settings.api_prefix)
    app.include_router(applications.router, prefix=settings.api_prefix)

    return app


app = create_app()

# AWS Lambda entry point — set handler to: backend.app.main.handler
handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=get_settings().api_gateway_base_path,
)
