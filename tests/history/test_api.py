import pytest
from app.models.user import User
from app.models.product import Product
from app.security.jwt import create_access_token
from app.security.password import hash_password
from core.history.service import AnalysisHistoryService


@pytest.fixture
def seeded_product_user(client, db_session):
    user = User(
        email="product_api_user@example.com",
        username="prod_api_user",
        hashed_password=hash_password("SecurePassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token({"sub": str(user.id), "username": user.username})

    product = Product(
        user_id=user.id,
        product_url="https://www.daraz.lk/products/api-test-prod.html",
        product_title="API Test Headset",
        platform="Daraz",
        overall_rating=4.8,
        total_reviews=25,
    )
    db_session.add(product)
    db_session.flush()

    history_svc = AnalysisHistoryService(db_session)
    history_svc.save_analysis(
        public_id="anl_api_001",
        user_id=user.id,
        product_id=product.id,
        business_risk_level="MEDIUM",
        quality_risk_score=30.0,
        delivery_risk_score=50.0,
        trust_risk_score=20.0,
        overall_business_risk_index=33.3,
    )

    return {
        "client": client,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": str(user.id),
        "product_id": str(product.id),
    }


def test_get_products_list_endpoint(seeded_product_user):
    client = seeded_product_user["client"]
    headers = seeded_product_user["headers"]

    res = client.get("/api/v1/products", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["items"]) >= 1
    assert data["items"][0]["productTitle"] == "API Test Headset"


def test_get_product_detail_endpoint(seeded_product_user):
    client = seeded_product_user["client"]
    headers = seeded_product_user["headers"]
    prod_id = seeded_product_user["product_id"]

    res = client.get(f"/api/v1/products/{prod_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == prod_id
    assert data["productTitle"] == "API Test Headset"


def test_get_product_history_and_latest(seeded_product_user):
    client = seeded_product_user["client"]
    headers = seeded_product_user["headers"]
    prod_id = seeded_product_user["product_id"]

    # History
    res_hist = client.get(f"/api/v1/products/{prod_id}/history", headers=headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()["data"]) >= 1

    # Latest
    res_latest = client.get(f"/api/v1/products/{prod_id}/latest", headers=headers)
    assert res_latest.status_code == 200
    assert res_latest.json()["data"]["analysisId"] == "anl_api_001"
