def test_authenticated_route_e2e(client):
    r = client.get("/authenticated-route")

    assert r.status_code == 200
    assert r.json() == {"message": "Hello user@example.com!"}
