import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    a_domain,
    ai,
    auth,
    companies,
    company_enrichment,
    container_calc,
    contacts,
    dashboard,
    field_visits,
    files,
    interactions,
    knowledge,
    leads,
    manufacturing_partners,
    market,
    object_interactions,
    objects_meta,
    orders,
    product_categories,
    products,
    quotations,
    rfqs,
    samples,
    tasks,
    users,
)
from app.api.v1.router import v1_router
from app.core.bootstrap import build_health_payload
from app.core.config import get_settings
from app.core.database_lifecycle import (
    PRODUCT_AUTO_MIGRATE_MODES,
    inspect_lifecycle_dev,
    start_desktop_lifecycle_thread,
)
from app.core.errors import ApiError
from app.core.request_id import RequestIdMiddleware, get_request_id
from app.core.responses import error_envelope
from app.core.version import APP_VERSION


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.started_at = datetime.now(timezone.utc).isoformat()
        app.state.dlm_lock = threading.Lock()
        app.state.dlm_snapshot = None
        app.state.dlm_progress = None
        if settings.APP_RUNTIME_MODE in PRODUCT_AUTO_MIGRATE_MODES:
            start_desktop_lifecycle_thread(app, settings, lock=app.state.dlm_lock)
        else:
            with app.state.dlm_lock:
                app.state.dlm_snapshot = inspect_lifecycle_dev(get_settings())
        app.state.bootstrap_health = build_health_payload(app.version, get_settings(), app=app)
        yield

    app = FastAPI(
        title="intelliOffice PartnerOS",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        if not request.url.path.startswith("/api/v1"):
            raise exc
        rid = get_request_id(request)
        return error_envelope(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=rid,
            status_code=exc.status_code,
        )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api")
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(dashboard.router)
    api.include_router(companies.router)
    api.include_router(company_enrichment.router)
    api.include_router(contacts.router)
    api.include_router(leads.router)
    api.include_router(a_domain.router)
    api.include_router(interactions.router)
    api.include_router(object_interactions.router_obj)
    api.include_router(tasks.router)
    api.include_router(tasks.object_tasks_router)
    api.include_router(objects_meta.router)
    api.include_router(objects_meta.notes_router)
    api.include_router(objects_meta.tags_attach_router)
    api.include_router(objects_meta.activity_router)
    api.include_router(manufacturing_partners.router)
    api.include_router(products.router)
    api.include_router(product_categories.router)
    api.include_router(files.router)
    api.include_router(files.objects_files_router)
    api.include_router(ai.router)
    api.include_router(field_visits.router)
    api.include_router(samples.router)
    api.include_router(rfqs.router)
    api.include_router(quotations.router)
    api.include_router(orders.router)
    api.include_router(market.router)
    api.include_router(knowledge.router)
    api.include_router(container_calc.router)

    app.include_router(api)
    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health")
    def health(request: Request) -> dict:
        return build_health_payload(request.app.version, get_settings(), app=request.app)

    return app


app = create_app()
