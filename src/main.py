"""FastAPI entry point for DSPy service."""

import hmac
import logging
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.api.routes import router
from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = get_settings()


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to verify internal API key for protected endpoints."""

    # Endpoints that don't require authentication
    PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # No key configured: fail CLOSED. This used to serve every protected route unauthenticated, which
        # made removing the key the same as opening the service. Local development opts in explicitly.
        if not settings.internal_api_key:
            if settings.allow_unauthenticated_dev:
                logger.warning("ALLOW_UNAUTHENTICATED_DEV set - serving without authentication")
                return await call_next(request)
            logger.error(f"No INTERNAL_API_KEY configured - refusing {request.url.path}")
            return JSONResponse(status_code=503, content={"detail": "Service authentication is not configured"})

        # Check for API key in header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

        # Handle Bearer token format
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]

        if not api_key:
            logger.warning(f"Missing API key for {request.url.path}")
            return JSONResponse(status_code=401, content={"detail": "Missing API key"})

        if not hmac.compare_digest(api_key.encode(), settings.internal_api_key.encode()):
            logger.warning(f"Invalid API key for {request.url.path}")
            return JSONResponse(status_code=403, content={"detail": "Invalid API key"})

        return await call_next(request)


# Create FastAPI app
app = FastAPI(
    title="DSPy Service",
    description="Prompt specification compilation service for Graffiticode",
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API key authentication middleware
app.add_middleware(APIKeyAuthMiddleware)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the service."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Listening on {settings.host}:{settings.port}")

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
