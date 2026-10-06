import pytest


@pytest.mark.asyncio
async def test_revivals_crud_and_ownership(client):
    # Register User A
    resp_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "password123"},
    )
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    resp_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "password123"},
    )
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A creates a Revival
    rev_payload = {
        "name": "Alex",
        "language": "en",
        "personality": "Funny + caring",
        "speaking_style": "Casual",
        "relationship_context": "Best friend",
        "voice_authorized": True,
    }
    create_resp = await client.post("/api/v1/revivals", json=rev_payload, headers=headers_a)
    assert create_resp.status_code == 201
    revival = create_resp.json()
    revival_id = revival["id"]
    assert revival["name"] == "Alex"
    assert revival["voice_authorized"] is True

    # 2. User A reads their Revival
    get_resp = await client.get(f"/api/v1/revivals/{revival_id}", headers=headers_a)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == revival_id

    # 3. User B attempts to access User A's Revival -> 404 (does not leak existence)
    bad_get = await client.get(f"/api/v1/revivals/{revival_id}", headers=headers_b)
    assert bad_get.status_code == 404

    # 4. User B attempts to update User A's Revival -> 404
    bad_patch = await client.patch(
        f"/api/v1/revivals/{revival_id}",
        json={"name": "Hacked Alex"},
        headers=headers_b,
    )
    assert bad_patch.status_code == 404

    # 5. User A updates Revival
    update_resp = await client.patch(
        f"/api/v1/revivals/{revival_id}",
        json={"personality": "Hilarious and supportive"},
        headers=headers_a,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["personality"] == "Hilarious and supportive"

    # 6. User A lists their Revivals
    list_resp = await client.get("/api/v1/revivals", headers=headers_a)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 7. User B lists Revivals -> empty list
    list_b = await client.get("/api/v1/revivals", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # 8. User A deletes Revival
    del_resp = await client.delete(f"/api/v1/revivals/{revival_id}", headers=headers_a)
    assert del_resp.status_code == 204

    # 9. Verify it is deleted
    assert (await client.get(f"/api/v1/revivals/{revival_id}", headers=headers_a)).status_code == 404
