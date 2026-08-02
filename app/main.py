from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config.settings import settings
from app.startup import startup_ai_engine
from app.utils.logger import api_logger
from app.utils.exceptions import (
    BaseBusinessException,
    business_exception_handler,
    general_exception_handler,
)
from app.middleware.request_id_middleware import RequestIDMiddleware
from app.middleware.logging_middleware import LoggingMiddleware

from app.api.routers.health import router as health_router
from app.api.routers.analysis import router as analysis_router
from app.api.routers.history import router as history_router
from app.api.routers.products import router as products_router
from app.api.routers.auth import router as auth_router
from app.api.routers.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager: Handles Application Startup & Shutdown Events.
    """
    api_logger.info("Initializing FastAPI Backend Application...")
    startup_ai_engine()
    yield
    api_logger.info("Shutting down FastAPI Backend Application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-Ready FastAPI Backend for AI Business Risk Analysis System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

from fastapi import Request

# Mount Static Assets Directory for Evaluation Prototype Demo SPA
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Custom Middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Global Exception Handlers
app.add_exception_handler(BaseBusinessException, business_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Root Redirect to Single Page Application Demo
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html")

# Register API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
