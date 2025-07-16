import json

def setup_user(client):
    client.post(
        "/api/auth/register",
        json={"username":"u2","email":"u2@example.com","password":"pw2"}
    )

def test_group_and_expense_flow(client):
    setup_user(client)

    # 1) Create a group
    resp = client.post(
        "/api/shared/groups",
        json={"name":"Trip","created_by":1,"members":[1]}
    )
    assert resp.status_code == 201
    gid = resp.get_json()["group_id"]

    # 2) Fetch that user's groups
    resp = client.get(f"/api/shared/groups/1")
    assert resp.status_code == 200
    assert any(g["group_id"] == gid for g in resp.get_json()["groups"])

    # 3) Add a shared expense
    resp = client.post(
        "/api/shared/expense",
        json={
            "description": "Dinner",
            "amount":  50,
            "group_id": gid,
            "paid_by":  1,
            "excluded_members": [],
            "context": ""
        }
    )
    assert resp.status_code == 201
    eid = resp.get_json()["expense_id"]

    # 4) Get group history (should include that expense)
    resp = client.get(f"/api/shared/group/{gid}/history")
    assert resp.status_code == 200
    assert any(e["id"] == eid for e in resp.get_json()["expenses"])

    # 5) Calculate balances & simplified transactions
    resp = client.get(f"/api/shared/group/{gid}/balances")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "net_balances" in data and "simplified_transactions" in data

    # 6) Delete the shared expense
    resp = client.delete(f"/api/shared/expense/{eid}")
    assert resp.status_code == 200
