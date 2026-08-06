import pytest
import concurrent.futures


def test_concurrent_multi_user_isolation(client):
    # 1. Register & Login User A
    r_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "userA_concurrent@example.com",
            "username": "user_a_conc",
            "password": "SecurePassword123!"
        }
    )
    if r_a.status_code == 200:
        token_a = r_a.json()["data"]["accessToken"]
    else:
        l_a = client.post(
            "/api/v1/auth/login",
            json={"emailOrUsername": "user_a_conc", "password": "SecurePassword123!"}
        )
        token_a = l_a.json()["data"]["accessToken"]

    # 2. Register & Login User B
    r_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "userB_concurrent@example.com",
            "username": "user_b_conc",
            "password": "SecurePassword123!"
        }
    )
    if r_b.status_code == 200:
        token_b = r_b.json()["data"]["accessToken"]
    else:
        l_b = client.post(
            "/api/v1/auth/login",
            json={"emailOrUsername": "user_b_conc", "password": "SecurePassword123!"}
        )
        token_b = l_b.json()["data"]["accessToken"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A and User B start analysis jobs concurrently
    def start_job_a():
        return client.post(
            "/api/v1/analysis/start",
            json={"productUrl": "https://www.daraz.lk/products/headphone-sample-a.html"},
            headers=headers_a
        )

    def start_job_b():
        return client.post(
            "/api/v1/analysis/start",
            json={"productUrl": "https://www.daraz.lk/products/headphone-sample-b.html"},
            headers=headers_b
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(start_job_a)
        future_b = executor.submit(start_job_b)

        res_a = future_a.result()
        res_b = future_b.result()

    assert res_a.status_code == 200, f"User A job creation failed: {res_a.text}"
    assert res_b.status_code == 200, f"User B job creation failed: {res_b.text}"

    job_id_a = res_a.json()["data"]["analysisId"]
    job_id_b = res_b.json()["data"]["analysisId"]

    assert job_id_a != job_id_b, "Job IDs must be distinct"

    # 4. Verify User A cannot access User B's job status (returns status UNKNOWN)
    cross_res = client.get(f"/api/v1/analysis/status/{job_id_b}", headers=headers_a)
    assert cross_res.status_code == 200
    assert cross_res.json()["data"]["status"] == "UNKNOWN", "User A must not be able to access User B's active job status"

    # 5. User A sends stop request -> Verify only User A's job is stopped
    stop_a = client.post("/api/v1/analysis/stop", json={"analysisId": job_id_a}, headers=headers_a)
    assert stop_a.status_code == 200
    assert stop_a.json()["data"]["stopRequested"] is True

    # User B's job status check should still show running/active status without stop_requested
    status_b = client.get(f"/api/v1/analysis/status/{job_id_b}", headers=headers_b)
    assert status_b.status_code == 200
    assert status_b.json()["data"]["analysisId"] == job_id_b
