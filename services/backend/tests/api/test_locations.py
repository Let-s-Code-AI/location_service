from sql_app import models

LOCATION = {"city": "Kraków", "street": "Floriańska", "latitude": 50.06, "longitude": 19.94}


async def test_create_location(client):
    response = await client.post("/locations/", json=LOCATION)

    assert response.status_code == 200
    body = response.json()
    assert body["location_id"] == 1
    assert body["city"] == "Kraków"


async def test_read_locations_supports_pagination(client):
    for i in range(3):
        await client.post("/locations/", json={"city": f"Miasto {i}"})

    response = await client.get("/locations/", params={"skip": 1, "limit": 1})

    assert response.status_code == 200
    assert [loc["city"] for loc in response.json()] == ["Miasto 1"]


async def test_read_location_not_found(client):
    response = await client.get("/locations/999")

    assert response.status_code == 404


async def test_patch_updates_only_sent_fields(client):
    created = (await client.post("/locations/", json=LOCATION)).json()

    response = await client.patch(
        f"/locations/{created['location_id']}", json={"street": "Grodzka"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["street"] == "Grodzka"
    assert body["city"] == "Kraków"  # pole spoza PATCH-a bez zmian


async def test_delete_location(client):
    created = (await client.post("/locations/", json=LOCATION)).json()

    response = await client.delete(f"/locations/{created['location_id']}")

    assert response.status_code == 204
    assert (await client.get(f"/locations/{created['location_id']}")).status_code == 404


async def test_delete_location_used_by_listing_returns_409(client, db):
    location = models.Location(city="Warszawa")
    building, owner, features = models.Building(), models.Owner(), models.Features()
    db.add_all([location, building, owner, features])
    await db.flush()
    db.add(
        models.Listing(
            location_id=location.location_id,
            building_id=building.building_id,
            owner_id=owner.owner_id,
            features_id=features.features_id,
        )
    )
    await db.commit()

    response = await client.delete(f"/locations/{location.location_id}")

    assert response.status_code == 409
