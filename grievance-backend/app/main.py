from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import me_router, router as auth_router
from .config import get_settings
from .routers import attachments, issues, staff
from .services.errors import ServiceError
from .security.csrf import csrf_protect


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_for_runtime()

    app = FastAPI(
        title="College Grievance API",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    if settings.cors_origin_list:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list,
                           allow_credentials=True, allow_methods=["*"],
                           allow_headers=["Content-Type", "X-CSRF-Token"])

    # Every route under the prefix gets CSRF protection.
    api = APIRouter(prefix=settings.api_prefix, dependencies=[Depends(csrf_protect)])
    api.include_router(auth_router)
    api.include_router(me_router)
    api.include_router(issues.router)
    api.include_router(attachments.router)
    api.include_router(staff.router)
    # Stage 3 adds: admin, classify, notifications.

    @api.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(api)

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail, **exc.extra})

    return app


app = create_app()
