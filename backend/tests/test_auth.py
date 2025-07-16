import json

def test_register_and_login(client):
    # Register
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email":    "test@example.com",
            "password": "pass123"
        },
    )
    assert resp.status_code == 201

    # Login
    resp = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "pass123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
