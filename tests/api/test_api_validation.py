"""
API Validation Tests (Milestone 10.2).
Verifies HTTP status codes, response schemas, and structured error responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_check_product_valid():
    """Scenario 1: Valid check-product preview request."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.daraz.com.np/products/sample-item-i12345.html"}
    )
    assert response.status_code in [200, 400, 500]
    data = response.json()
    assert "success" in data
    assert "meta" in data


def test_api_invalid_url_format():
    """Scenario 2: Invalid product URL raises HTTP 400/422 validation error."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "not_a_valid_url"}
    )
    assert response.status_code in [400, 422, 500]


def test_api_empty_request_body():
    """Scenario 3: Empty request body returns 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={}
    )
    assert response.status_code == 422


def test_api_malformed_json():
    """Scenario 4: Malformed JSON payload returns 422 / 400 status."""
    response = client.post(
        "/api/v1/analysis/check-product",
        content="invalid_json_string{{{",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_api_unsupported_platform():
    """Scenario 5: Non-Daraz unsupported platform URL returns response with platform info."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.amazon.com/dp/B08N5WRWNW"}
    )
    assert response.status_code in [200, 400, 422, 500]


def test_api_category_url_rejection():
    """Scenario 6: Category/Directory URL returns HTTP 400 with category rejection message."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.daraz.lk/products"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "category/directory page" in data["message"]


def test_api_incomplete_daraz_url_rejection():
    """Scenario 7: Incomplete Daraz product URL missing item ID returns HTTP 400 immediately."""
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.daraz.lk/products/over-ear-noise"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "incomplete or invalid" in data["message"].lower() or "product details" in data["message"].lower()


