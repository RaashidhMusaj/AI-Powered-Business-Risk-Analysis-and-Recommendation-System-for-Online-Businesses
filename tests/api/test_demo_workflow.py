import pytest


def test_check_product_endpoint(client):
    response = client.post(
        "/api/v1/analysis/check-product",
        json={"productUrl": "https://www.daraz.lk/products/sample.html"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "title" in data["data"]
    assert "platform" in data["data"]


def test_start_analysis_job(client):
    # Register / login test user for guided demo workflow test
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "demoworkflow@example.com",
            "username": "demoworkflow_user",
            "password": "password123",
            "fullName": "Demo Workflow User"
        }
    )
    if reg_res.status_code == 200:
        token = reg_res.json()["data"]["accessToken"]
    else:
        login_res = client.post(
            "/api/v1/auth/login",
            json={"emailOrUsername": "demoworkflow_user", "password": "password123"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["data"]["accessToken"]

    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/analysis/start",
        json={"productUrl": "https://www.daraz.lk/products/sample.html"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "analysisId" in data["data"]
    assert data["data"]["status"] == "SCRAPING"

    analysis_id = data["data"]["analysisId"]

    # Test Status Polling Endpoint
    status_res = client.get(f"/api/v1/analysis/status/{analysis_id}", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["success"] is True
    assert "currentStep" in status_data["data"]
    assert "reviewsCollected" in status_data["data"]

    # Test Finish Scraping ("Q" Key Equivalent Stop)
    stop_res = client.post(
        "/api/v1/analysis/stop",
        json={"analysisId": analysis_id},
        headers=headers
    )
    assert stop_res.status_code == 200
    stop_data = stop_res.json()
    assert stop_data["success"] is True
    assert stop_data["data"]["stopRequested"] is True
