"""
Routers package.
"""
from app.api.routers.health import router as health_router
from app.api.routers.analysis import router as analysis_router
from app.api.routers.history import router as history_router
from app.api.routers.products import router as products_router
from app.api.routers.auth import router as auth_router
from app.api.routers.profile import router as profile_router

__all__ = [
    "health_router",
    "analysis_router",
    "history_router",
    "products_router",
    "auth_router",
    "profile_router",
]
