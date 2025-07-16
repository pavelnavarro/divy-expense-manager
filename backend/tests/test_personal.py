import json
from datetime import datetime

def get_token(client):
    client.post(
        "/api/auth/register",
        json={"username":"u1","email":"u1@example.com","password":"pw"}
    )
    login = client.post(
        "/api/auth/login",
        json={"username":"u1","password":"pw"}
    )
    return login.get_json()["access_token"]

def test_personal_crud(client):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1) Add an expense
    payload = {
        "amount": 12.34,
        "description": "Coffee",
        "transaction_date": datetime.utcnow().isoformat(),
        "is_recurring": False
    }
    
    resp = client.post("/api/personal/expenses", json=payload, headers=headers)
    print("STATUS:", resp.status_code)
    print("BODY:", resp.get_data(as_text=True))  # Esto mostrará el error
    assert resp.status_code == 201
    
    data = resp.get_json()
    eid = data["expense"]["id"]

    # 2) List expenses
    resp = client.get("/api/personal/expenses", headers=headers)
    assert resp.status_code == 200
    exps = resp.get_json()["expenses"]
    assert any(e["id"] == eid for e in exps)

    # 3) Delete the expense
    resp = client.delete(f"/api/personal/expenses/{eid}", headers=headers)
    assert resp.status_code == 200

    # 4) Confirm it's gone
    resp = client.get("/api/personal/expenses", headers=headers)
    assert all(e["id"] != eid for e in resp.get_json()["expenses"])
