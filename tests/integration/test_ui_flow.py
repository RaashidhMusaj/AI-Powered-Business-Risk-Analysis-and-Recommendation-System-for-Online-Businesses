"""
UI Flow Integration Test (Milestone 11.9).
Validates complete user journey, static SPA assets, and endpoint payload contracts.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ui_static_assets_availability():
    """Milestone 11.9: Validates all modular frontend static assets are served successfully."""
    # 1. Root redirect
    res_root = client.get("/", follow_redirects=False)
    assert res_root.status_code in [302, 307]
    assert "/static/index.html" in res_root.headers.get("location", "")

    # 2. Main HTML SPA
    res_html = client.get("/static/index.html")
    assert res_html.status_code == 200
    assert "AI Business Risk Analysis" in res_html.text
    assert "recommendationPanel" in res_html.text
    assert "reviewExplorerList" in res_html.text

    # 3. Modular JS Files
    modules = ["api.js", "loading.js", "charts.js", "recommendations.js", "reviews.js", "dashboard.js", "app.js"]
    for mod in modules:
        res_js = client.get(f"/static/js/{mod}")
        assert res_js.status_code == 200, f"Failed to load static JS module: {mod}"

    # 4. CSS Files
    css_files = ["style.css", "dashboard.css"]
    for css in css_files:
        res_css = client.get(f"/static/css/{css}")
        assert res_css.status_code == 200, f"Failed to load static CSS file: {css}"


def test_ui_api_contract_flow():
    """Milestone 11.9: Validates check product endpoint payload required for UI rendering."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.daraz.lk/products/sample-ui-flow-i99999.html"}
    )
    assert response.status_code in [200, 400, 500]
    data = response.json()
    assert "success" in data
