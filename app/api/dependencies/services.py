from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.services.health_service import HealthService
from app.services.analysis_service import AnalysisService
from app.services.auth_service import AuthService
from app.repositories.health_repository import HealthRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository

from core.recommendation.service import RecommendationService


def get_health_service(db: Session = Depends(get_db)) -> HealthService:
    """
    Dependency providing HealthService instance with DB session.
    """
    health_repo = HealthRepository(db=db)
    return HealthService(health_repo=health_repo)


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    """
    Dependency providing AnalysisService instance with DB session and repositories.
    """
    product_repo = ProductRepository(db=db)
    analysis_repo = AnalysisRepository(db=db)
    review_repo = ReviewRepository(db=db)
    return AnalysisService(
        db=db,
        product_repo=product_repo,
        analysis_repo=analysis_repo,
        review_repo=review_repo,
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency providing AuthService instance with DB session.
    """
    user_repo = UserRepository(db=db)
    return AuthService(db=db, user_repo=user_repo)


def get_recommendation_service() -> RecommendationService:
    """
    Dependency providing RecommendationService instance.
    """
    return RecommendationService()
