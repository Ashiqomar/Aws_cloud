"""
FastAPI application factory.

Mounts versioned routers and configures middleware / lifespan events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.aws import router as aws_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.costs import router as costs_router
from app.api.v1.ai import router as ai_router
from app.api.v1.remediate import router as remediate_router

settings = get_settings()

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("🚀  %s starting up …", settings.APP_NAME)
    yield
    logger.info("🛑  %s shutting down …", settings.APP_NAME)


# ── App instance ─────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "FinOps platform backend — multi-tenant AWS cost visibility, "
        "resource inventory, and savings recommendations."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow all origins during development) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(aws_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(costs_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(remediate_router, prefix="/api/v1")


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """Quick liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME}
