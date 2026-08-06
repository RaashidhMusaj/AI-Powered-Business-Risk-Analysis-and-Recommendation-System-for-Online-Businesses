import pytest


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] == "healthy"
    assert data["data"]["model_loaded"] is True
    assert "checks" in data["data"]
    assert "meta" in data
    assert "requestId" in data["meta"]


def test_version_endpoint(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["appName"] == "AI Business Risk Analysis System"
    assert data["data"]["version"] == "1.0.0"


def test_auth_register_and_login_live(client):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testendpoint@example.com",
            "username": "testendpoint_user",
            "password": "SecurePassword123!",
            "fullName": "Endpoint Tester"
        }
    )
    if reg_res.status_code == 200:
        token = reg_res.json()["data"]["accessToken"]
    else:
        login_res = client.post(
            "/api/v1/auth/login",
            json={"emailOrUsername": "testendpoint_user", "password": "SecurePassword123!"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["data"]["accessToken"]

    profile_res = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_res.status_code == 200
    assert profile_res.json()["data"]["username"] == "testendpoint_user"


def test_analysis_invalid_url_with_auth(client):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalidurl_test@example.com",
            "username": "invalidurl_user",
            "password": "SecurePassword123!"
        }
    )
    if reg_res.status_code == 200:
        token = reg_res.json()["data"]["accessToken"]
    else:
        login_res = client.post(
            "/api/v1/auth/login",
            json={"emailOrUsername": "invalidurl_user", "password": "SecurePassword123!"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["data"]["accessToken"]

    response = client.post(
        "/api/v1/analysis",
        json={"productUrl": "invalid-url-string"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data
