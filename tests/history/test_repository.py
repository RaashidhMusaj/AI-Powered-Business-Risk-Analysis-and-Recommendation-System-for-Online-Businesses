import pytest
import uuid
from app.models.user import User
from app.models.product import Product
from core.history.repository import AnalysisHistoryRepository


def test_history_repository_save_and_find(db_session):
    user = User(email="repouser@example.com", username="repouser", hashed_password="hashed_pass")
    db_session.add(user)
    db_session.flush()

    product = Product(user_id=user.id, product_url="https://www.daraz.lk/products/repo-item.html", product_title="Repo Item")
    db_session.add(product)
    db_session.flush()

    repo = AnalysisHistoryRepository(db_session)
    saved = repo.save({
        "public_id": "anl_repo_001",
        "user_id": user.id,
        "product_id": product.id,
        "business_risk_level": "MEDIUM",
        "quality_risk_score": 25.0,
        "delivery_risk_score": 60.0,
        "trust_risk_score": 30.0,
        "overall_business_risk_index": 38.3,
        "business_risk_snapshot": {"level": "MEDIUM"},
        "recommendation_snapshot": {"summary": "Fix delivery"},
    })

    assert saved.public_id == "anl_repo_001"

    found = repo.find_by_public_id("anl_repo_001", user.id)
    assert found is not None
    assert found.business_risk_index == 38.3
    assert found.business_risk_snapshot["level"] == "MEDIUM"

    count = repo.count(user.id)
    assert count == 1
