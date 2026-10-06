import pytest


@pytest.mark.asyncio
async def test_memories_crud_and_isolation(client):
    reg = await client.post("/api/v1/auth/register", json={"email": "mem_user@test.com", "password": "password123"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rev = await client.post("/api/v1/revivals", json={"name": "MemoryBot", "language": "en"}, headers=headers)
    rev_id = rev.json()["id"]

    # 1. Create memories with different importance
    m1 = await client.post(
        f"/api/v1/revivals/{rev_id}/memories",
        json={"memory_text": "Loves pistachio ice cream", "importance": "high"},
        headers=headers,
    )
    assert m1.status_code == 201
    m1_id = m1.json()["id"]

    m2 = await client.post(
        f"/api/v1/revivals/{rev_id}/memories",
        json={"memory_text": "Works as a software engineer", "importance": "medium"},
        headers=headers,
    )
    assert m2.status_code == 201

    # 2. List memories
    list_resp = await client.get(f"/api/v1/revivals/{rev_id}/memories", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    # 3. Delete memory
    del_resp = await client.delete(f"/api/v1/memories/{m1_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify only 1 remains
    list_after = await client.get(f"/api/v1/revivals/{rev_id}/memories", headers=headers)
    assert len(list_after.json()) == 1
