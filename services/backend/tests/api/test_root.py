async def test_root_returns_status(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}
