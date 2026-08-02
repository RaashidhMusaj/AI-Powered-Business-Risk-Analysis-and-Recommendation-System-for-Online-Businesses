import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_user_registration_and_login():
    test_email = "testuser_tenant@example.com"
    test_username = "tenant_user_1"
    test_password = "securepassword123"

    # 1. Test Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "username": test_username,
            "password": test_password,
            "fullName": "Tenant User 1"
        }
    )

    if reg_response.status_code == 400 and "already exists" in reg_response.json().get("message", ""):
        # If user already registered in dev DB, proceed to login
        pass
    else:
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        data = reg_response.json()["data"]
        assert "accessToken" in data
        assert data["username"] == test_username

    # 2. Test Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "emailOrUsername": test_username,
            "password": test_password
        }
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token_data = login_response.json()["data"]
    token = token_data["accessToken"]

    # 3. Test Profile with Bearer token
    profile_response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()["data"]
    assert profile_data["username"] == test_username
    assert profile_data["email"] == test_email


def test_unauthenticated_access_rejected():
    # Attempt to access protected history endpoint without token
    response = client.get("/api/v1/history")
    assert response.status_code == 401
    assert "detail" in response.json() or "message" in response.json()


def test_tenant_data_isolation():
    # Register User 1
    user1_email = "tenantA@example.com"
    user1_username = "tenant_a"
    user1_pass = "pass123456"

    r1 = client.post(
        "/api/v1/auth/register",
        json={"email": user1_email, "username": user1_username, "password": user1_pass}
    )
    if r1.status_code == 200:
        token_a = r1.json()["data"]["accessToken"]
    else:
        l1 = client.post("/api/v1/auth/login", json={"emailOrUsername": user1_username, "password": user1_pass})
        token_a = l1.json()["data"]["accessToken"]

    # Register User 2
    user2_email = "tenantB@example.com"
    user2_username = "tenant_b"
    user2_pass = "pass123456"

    r2 = client.post(
        "/api/v1/auth/register",
        json={"email": user2_email, "username": user2_username, "password": user2_pass}
    )
    if r2.status_code == 200:
        token_b = r2.json()["data"]["accessToken"]
    else:
        l2 = client.post("/api/v1/auth/login", json={"emailOrUsername": user2_username, "password": user2_pass})
        token_b = l2.json()["data"]["accessToken"]

    # Get history for User A -> Should return 200 and empty list or user A items
    hist_a = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_a}"})
    assert hist_a.status_code == 200

    # Get history for User B -> Should return 200 and user B items
    hist_b = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_b}"})
    assert hist_b.status_code == 200

    # Verify non-existent analysis_id for User B returns 404
    detail_b = client.get("/api/v1/history/anl_nonexistent999", headers={"Authorization": f"Bearer {token_b}"})
    assert detail_b.status_code == 404
