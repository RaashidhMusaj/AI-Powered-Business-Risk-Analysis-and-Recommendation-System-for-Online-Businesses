import pytest
from app.models.user import User
from app.models.product import Product
from app.models.analysis import Analysis
from app.models.review import Review
from app.security.jwt import create_access_token
from app.security.password import hash_password


@pytest.fixture
def seeded_client(client, db_session):
    # Seed sample user
    user = User(
        email="seeded@example.com",
        username="seeded_user",
        hashed_password=hash_password("SecurePassword123!"),
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token({"sub": str(user.id), "username": user.username})

    # Seed sample data owned by seeded user
    product = Product(
        user_id=user.id,
        product_url="https://www.daraz.lk/products/test-headphones.html",
        product_title="Wireless Over-Ear Headphones",
        platform="Daraz",
        overall_rating=4.5,
        total_reviews=15
    )
    db_session.add(product)
    db_session.flush()

    analysis = Analysis(
        public_id="anl_sample123",
        user_id=user.id,
        product_id=product.id,
        status="completed",
        execution_duration_ms=250.0,
        quality_risk_score=12.5,
        delivery_risk_score=18.0,
        trust_risk_score=10.0,
        business_risk_index=13.5,
        business_risk_level="LOW",
        total_reviews=15,
        total_positive_reviews=12,
        total_negative_reviews=2,
        total_neutral_reviews=1,
        average_confidence=0.91,
        aspect_statistics={"quality": {"mention_ratio": 0.5}},
        confidence_statistics={"average_confidence": 0.91},
        risk_breakdown={"overall": "LOW"}
    )
    db_session.add(analysis)
    db_session.flush()

    review = Review(
        user_id=user.id,
        analysis_id=analysis.id,
        review_text="Sound quality is clear and battery lasts long.",
        sentiment="POSITIVE",
        confidence_score=0.95
    )
    db_session.add(review)
    db_session.commit()

    return client, token


def test_get_history_list(seeded_client):
    client, token = seeded_client
    response = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert len(data["data"]["items"]) == 1
    item = data["data"]["items"][0]
    assert item["analysisId"] == "anl_sample123"
    assert item["businessRiskLevel"] == "LOW"


def test_get_history_detail(seeded_client):
    client, token = seeded_client
    response = client.get("/api/v1/history/anl_sample123", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    detail = data["data"]
    assert detail["analysisId"] == "anl_sample123"
    assert detail["product"]["title"] == "Wireless Over-Ear Headphones"
    assert detail["risks"]["businessRiskLevel"] == "LOW"
    assert len(detail["reviews"]) == 1


def test_get_history_detail_not_found(seeded_client):
    client, token = seeded_client
    response = client.get("/api/v1/history/anl_nonexistent", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_get_products_list(seeded_client):
    client, token = seeded_client
    response = client.get("/api/v1/products", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["productTitle"] == "Wireless Over-Ear Headphones"


def test_delete_history_item(seeded_client):
    client, token = seeded_client
    # Delete item
    del_res = client.delete("/api/v1/history/anl_sample123", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify item no longer exists
    get_res = client.get("/api/v1/history/anl_sample123", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 404
