"""
Lexra Engine - Backend API
Enterprise AI contract intelligence platform
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import contracts, analysis, clauses, auth, cuad_analysis
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.limiter import limiter
from app.services.auth_service import init_auth_tables
from app.services.database_factory import database_service as db_service
from app.services.task_queue import task_queue

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting CLM API Server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    # Initialize auth tables (creates demo user if needed)
    try:
        init_auth_tables()
        logger.info("Auth tables initialized")
    except Exception as e:
        logger.error(f"Auth table init failed (non-fatal): {e}")

    # Recover stale statuses left in-flight by reloads/crashes.
    try:
        recover_fn = getattr(db_service, "recover_stuck_contracts", None)
        if callable(recover_fn):
            recovered = await recover_fn()
            recovered_total = (
                sum(recovered.values())
                if isinstance(recovered, dict)
                else int(recovered or 0)
            )
            if recovered_total:
                logger.warning(
                    f"Recovered {recovered_total} stale contract status(es): {recovered}"
                )
    except Exception as e:
        logger.error(f"Stale contract recovery failed (non-fatal): {e}")

    task_queue.start()
    logger.info("Task queue started")
    yield
    logger.info("Shutting down CLM API Server...")
    await task_queue.stop()


# Initialize FastAPI app
app = FastAPI(
    title="Lexra API",
    description="Enterprise contract intelligence engine with AI-powered extraction, risk analysis, and document understanding",
    version="1.0.0",
    lifespan=lifespan
)

# Attach rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenTelemetry tracing (no-op in dev when OTEL_EXPORTER_OTLP_ENDPOINT is unset)
from app.core.tracing import setup_tracing
setup_tracing(app)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and response status for debugging."""
    logger.info(f"→ {request.method} {request.url.path} from {request.client.host if request.client else '?'}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} → {response.status_code}")
    return response


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "CLM API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    import httpx
    ollama_status = "offline"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                ollama_status = "connected"
    except Exception:
        pass
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "azure_configured": bool(settings.AZURE_OPENAI_ENDPOINT),
        "ollama": ollama_status,
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(clauses.router, prefix="/api/clauses", tags=["Clauses"])
app.include_router(cuad_analysis.router, prefix="/api/contracts", tags=["CUAD Analysis"])


# Handle response serialization errors gracefully (e.g. Pydantic validation)
@app.exception_handler(ResponseValidationError)
async def response_validation_handler(request: Request, exc: ResponseValidationError):
    logger.error(f"Response validation error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Response serialization failed. This is a server bug."}
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
