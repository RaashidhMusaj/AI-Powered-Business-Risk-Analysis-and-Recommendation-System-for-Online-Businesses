import pytest
from app.models.user import User
from app.models.product import Product
from app.security.jwt import create_access_token
from app.security.password import hash_password
from core.history.service import AnalysisHistoryService


@pytest.fixture
def seeded_trend_user(client, db_session):
    user = User(
        email="trend_user@example.com",
        username="trend_user",
        hashed_password=hash_password("SecurePassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token({"sub": str(user.id), "username": user.username})

    product = Product(
        user_id=user.id,
        product_url="https://www.daraz.lk/products/trend-test.html",
        product_title="Trend Test Product",
    )
    db_session.add(product)
    db_session.flush()

    history_svc = AnalysisHistoryService(db_session)
    history_svc.save_analysis(
        public_id="anl_trend_1",
        user_id=user.id,
        product_id=product.id,
        business_risk_level="HIGH",
        quality_risk_score=80.0,
        delivery_risk_score=60.0,
        trust_risk_score=40.0,
        overall_business_risk_index=60.0,
    )
    history_svc.save_analysis(
        public_id="anl_trend_2",
        user_id=user.id,
        product_id=product.id,
        business_risk_level="MEDIUM",
        quality_risk_score=50.0,
        delivery_risk_score=40.0,
        trust_risk_score=30.0,
        overall_business_risk_index=40.0,
    )

    return {
        "client": client,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": str(user.id),
        "product_id": str(product.id),
    }


def test_trend_api_response_format(seeded_trend_user):
    client = seeded_trend_user["client"]
    headers = seeded_trend_user["headers"]
    prod_id = seeded_trend_user["product_id"]

    res = client.get(f"/api/v1/products/{prod_id}/trend", headers=headers)
    assert res.status_code == 200
    points = res.json()["data"]

    assert isinstance(points, list)
    assert len(points) == 2

    point = points[0]
    assert "date" in point
    assert "delivery" in point
    assert "quality" in point
    assert "trust" in point
    assert "bri" in point
    assert point["quality"] == 80.0
    assert point["bri"] == 60.0


def test_compare_api_response(seeded_trend_user):
    client = seeded_trend_user["client"]
    headers = seeded_trend_user["headers"]
    prod_id = seeded_trend_user["product_id"]

    res = client.get(
        f"/api/v1/products/{prod_id}/compare?from=anl_trend_1&to=anl_trend_2",
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["fromAnalysisId"] == "anl_trend_1"
    assert data["toAnalysisId"] == "anl_trend_2"
    assert data["deltas"]["quality"] == -30.0
    assert data["deltas"]["delivery"] == -20.0
    assert data["deltas"]["trust"] == -10.0
    assert data["deltas"]["bri"] == -20.0
