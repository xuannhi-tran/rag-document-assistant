import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import config
from app.routes.health import router as health_router
from app.routes.upload import router as upload_router
from app.routes.ask import router as ask_router
from app.routes.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    purge_task = None
    if config.RUN_STARTUP_TASKS:
        from app.create_tables import ensure_schema
        from app.services.embedding import get_model
        from app.services.cleanup import purge_loop
        ensure_schema()  # idempotent migration for existing deployments
        get_model()
        purge_task = asyncio.create_task(purge_loop())
    yield
    if purge_task:
        purge_task.cancel()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(documents_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,  # no cookies; the session id travels in X-Session-Id
    allow_methods=["*"],
    allow_headers=["*"],
)
