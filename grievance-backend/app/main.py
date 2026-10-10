import logging
import threading
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import me_router, router as auth_router
from .config import get_settings
from .routers import admin_config, admin_ops, attachments, classify, issues, notifications, staff
from .services.errors import ServiceError
from .security.csrf import csrf_protect


def _watchdog_loop(stop: threading.Event) -> None:
    """Checks every 5 minutes that the background worker is alive; emails the admin once if not."""
    from .db import SessionLocal
    from .services.scheduler import check_heartbeat
    while not stop.wait(300):
        try:
            with SessionLocal() as db:
                check_heartbeat(db)
        except Exception:
            logging.getLogger("grievance.watchdog").exception("watchdog check failed")


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_for_runtime()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop = threading.Event()
        if settings.watchdog_enabled:
            threading.Thread(target=_watchdog_loop, args=(stop,), daemon=True).start()
        yield
        stop.set()

    app = FastAPI(lifespan=lifespan, 
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
    api.include_router(classify.router)
    api.include_router(notifications.router)
    api.include_router(admin_config.router)
    api.include_router(admin_ops.router)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(api)

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail, **exc.extra})

    return app


app = create_app()
