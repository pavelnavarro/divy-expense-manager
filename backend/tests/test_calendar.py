def test_calendar_routes(client):
    # test /test
    resp = client.get("/api/calendar/test")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Calendar routes OK"

    # test /health
    resp = client.get("/api/calendar/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
