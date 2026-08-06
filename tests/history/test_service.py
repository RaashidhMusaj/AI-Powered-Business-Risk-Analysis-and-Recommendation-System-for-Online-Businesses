import pytest
from app.models.user import User
from app.models.product import Product
from core.history.service import AnalysisHistoryService
from core.history.exceptions import HistoryNotFoundError


def test_history_service_save_and_trend(db_session):
    user = User(email="serviceuser@example.com", username="serviceuser", hashed_password="hashed_pass")
    db_session.add(user)
    db_session.flush()

    product = Product(user_id=user.id, product_url="https://www.daraz.lk/products/service-item.html", product_title="Service Item")
    db_session.add(product)
    db_session.flush()

    service = AnalysisHistoryService(db_session)

    # Save run 1
    res1 = service.save_analysis(
        public_id="anl_svc_001",
        user_id=user.id,
        product_id=product.id,
        business_risk_level="HIGH",
        quality_risk_score=70.0,
        delivery_risk_score=65.0,
        trust_risk_score=40.0,
        overall_business_risk_index=58.3,
        business_risk_snapshot={"overallRiskLevel": "HIGH"},
        recommendation_snapshot={"count": 3},
    )
    assert res1["analysisId"] == "anl_svc_001"

    # Save run 2
    res2 = service.save_analysis(
        public_id="anl_svc_002",
        user_id=user.id,
        product_id=product.id,
        business_risk_level="MEDIUM",
        quality_risk_score=50.0,
        delivery_risk_score=45.0,
        trust_risk_score=30.0,
        overall_business_risk_index=41.6,
        business_risk_snapshot={"overallRiskLevel": "MEDIUM"},
        recommendation_snapshot={"count": 2},
    )
    assert res2["analysisId"] == "anl_svc_002"

    # Test Trend Data formatting (array of objects)
    trends = service.get_trend_data(user_id=user.id, product_id=product.id)
    assert len(trends) == 2
    assert isinstance(trends, list)
    assert "date" in trends[0]
    assert "delivery" in trends[0]
    assert "quality" in trends[0]
    assert "trust" in trends[0]
    assert "bri" in trends[0]

    # Test Side-by-Side Comparison Engine
    comp = service.compare_analyses(user_id=user.id, from_id="anl_svc_001", to_id="anl_svc_002")
    assert comp["fromAnalysisId"] == "anl_svc_001"
    assert comp["toAnalysisId"] == "anl_svc_002"
    assert comp["deltas"]["quality"] == -20.0
    assert comp["deltas"]["delivery"] == -20.0
    assert comp["deltas"]["trust"] == -10.0
    assert comp["deltas"]["bri"] == -16.7
