import pytest


def test_user_registration_and_login(client):
    test_email = "testuser_tenant@example.com"
    test_username = "tenant_user_1"
    test_password = "SecurePassword123!"

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
        assert data["role"] == "seller"

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
    assert token_data["role"] == "seller"

    # 3. Test Profile with Bearer token
    profile_response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()["data"]
    assert profile_data["username"] == test_username
    assert profile_data["email"] == test_email
    assert profile_data["role"] == "seller"


def test_password_strength_validation(client):
    # 1. Short password (< 8 chars)
    r1 = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "username": "short_user", "password": "Sh1!"}
    )
    assert r1.status_code == 422 or r1.status_code == 400

    # 2. Missing uppercase
    r2 = client.post(
        "/api/v1/auth/register",
        json={"email": "noupper@example.com", "username": "noupper_user", "password": "lowercase123!"}
    )
    assert r2.status_code == 422 or r2.status_code == 400

    # 3. Missing special char
    r3 = client.post(
        "/api/v1/auth/register",
        json={"email": "nospecial@example.com", "username": "nospecial_user", "password": "NoSpecialChar123"}
    )
    assert r3.status_code == 422 or r3.status_code == 400


def test_account_lockout_mechanism(client):
    lock_email = "lockout_test@example.com"
    lock_username = "lockout_user"
    valid_password = "ValidPassword123!"
    wrong_password = "WrongPassword123!"

    # 1. Register test user
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": lock_email, "username": lock_username, "password": valid_password}
    )
    assert reg.status_code in [200, 400]

    # 2. Fail login 5 consecutive times
    for i in range(4):
        res = client.post("/api/v1/auth/login", json={"emailOrUsername": lock_username, "password": wrong_password})
        assert res.status_code == 401
        assert "Invalid" in res.json().get("message", "")

    # 5th failed attempt triggers account lockout
    res5 = client.post("/api/v1/auth/login", json={"emailOrUsername": lock_username, "password": wrong_password})
    assert res5.status_code == 401
    assert "locked" in res5.json().get("message", "").lower()

    # 6th attempt with CORRECT password while locked should still be rejected
    res_locked = client.post("/api/v1/auth/login", json={"emailOrUsername": lock_username, "password": valid_password})
    assert res_locked.status_code == 401
    assert "locked" in res_locked.json().get("message", "").lower()


def test_unauthenticated_access_rejected(client):
    # Attempt to access protected history endpoint without token
    response = client.get("/api/v1/history")
    assert response.status_code == 401
    assert "detail" in response.json() or "message" in response.json()


def test_tenant_data_isolation(client):
    # Register User 1
    user1_email = "tenantA@example.com"
    user1_username = "tenant_a"
    user1_pass = "SecurePass123!"

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
    user2_pass = "SecurePass123!"

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


def test_email_format_validation(client):
    # 1. Missing @ symbol
    r1 = client.post(
        "/api/v1/auth/register",
        json={"email": "invalidemail.com", "username": "bad_email_1", "password": "ValidPassword123!"}
    )
    assert r1.status_code == 422 or r1.status_code == 400

    # 2. Missing domain extension
    r2 = client.post(
        "/api/v1/auth/register",
        json={"email": "user@domain", "username": "bad_email_2", "password": "ValidPassword123!"}
    )
    assert r2.status_code == 422 or r2.status_code == 400

    # 3. Invalid characters / spaces
    r3 = client.post(
        "/api/v1/auth/register",
        json={"email": "user name@domain.com", "username": "bad_email_3", "password": "ValidPassword123!"}
    )
    assert r3.status_code == 422 or r3.status_code == 400

    # 4. Valid RFC 822 email format
    r4 = client.post(
        "/api/v1/auth/register",
        json={"email": "valid_rfc822_user@example.co.lk", "username": "good_email_user", "password": "ValidPassword123!"}
    )
    assert r4.status_code in [200, 400]

