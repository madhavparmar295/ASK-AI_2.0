from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import me_router, router as auth_router
from .config import get_settings
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
    # Stage 2 adds: tickets, staff.   Stage 3 adds: admin, classify, notifications.

    @api.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(api)
    return app


app = create_app()
