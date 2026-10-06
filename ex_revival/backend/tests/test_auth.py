import pytest


@pytest.mark.asyncio
async def test_auth_registration_and_login(client):
    # 1. Valid registration
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "alex@example.com", "password": "supersecurepassword123"},
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["email"] == "alex@example.com"
    token = data["access_token"]

    # 2. Duplicate registration fails
    dup_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "alex@example.com", "password": "anotherpassword"},
    )
    assert dup_resp.status_code == 400

    # 3. Short password validation fails
    short_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert short_resp.status_code == 422

    # 4. Valid login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "supersecurepassword123"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # 5. Invalid login password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401

    # 6. Authenticated /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alex@example.com"

    # 7. Unauthorized /me access
    unauth_resp = await client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401
