"""Testy GET /listings/ — lista ogłoszeń z filtrami wyszukiwarki."""
from sql_app import models


async def make_listing(db, *, city, street=None, district=None, price=None, rooms=None, area=None):
    location = models.Location(city=city, street=street, city_district=district)
    building, owner, features = models.Building(), models.Owner(), models.Features()
    db.add_all([location, building, owner, features])
    await db.flush()
    listing = models.Listing(
        location_id=location.location_id,
        building_id=building.building_id,
        owner_id=owner.owner_id,
        features_id=features.features_id,
        price_total_zl=price,
        rooms=rooms,
        area=area,
        description_text="opis",
        url="https://example.com/1",
    )
    db.add(listing)
    await db.commit()
    return listing.listing_id


async def seed(db):
    await make_listing(db, city="Warszawa", street="Puławska", district="Mokotów", price=900_000, rooms=3, area=60)
    await make_listing(db, city="Kraków", street="Floriańska", price=650_000, rooms=2, area=45)
    await make_listing(db, city="Gdańsk", street="Długa", price=500_000, rooms=1, area=30)


def ids(response):
    assert response.status_code == 200, response.text
    return [item["location"]["city"] for item in response.json()]


async def test_empty_db_returns_empty_list(client):
    response = await client.get("/listings/")

    assert response.status_code == 200
    assert response.json() == []


async def test_returns_summary_without_details(client, db):
    await make_listing(db, city="Warszawa", street="Puławska", price=900_000, rooms=3, area=60.5)

    body = (await client.get("/listings/")).json()

    assert body == [
        {
            "listing_id": 1,
            "rooms": 3,
            "area": 60.5,
            "price_total_zl": 900_000,
            "location": {"city": "Warszawa", "city_district": None, "street": "Puławska"},
        }
    ]
    assert "description_text" not in body[0]
    assert "url" not in body[0]


async def test_q_matches_city_case_insensitive(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"q": "warsz"})) == ["Warszawa"]


async def test_q_matches_street_and_district(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"q": "Floria"})) == ["Kraków"]
    assert ids(await client.get("/listings/", params={"q": "Mokot"})) == ["Warszawa"]


async def test_q_without_matches_returns_empty(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"q": "Poznań"})) == []


async def test_price_range(client, db):
    await seed(db)

    response = await client.get("/listings/", params={"price_min": 600_000, "price_max": 800_000})

    assert ids(response) == ["Kraków"]


async def test_rooms_min(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"rooms_min": 2})) == ["Warszawa", "Kraków"]


async def test_area_range(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"area_min": 40, "area_max": 50})) == ["Kraków"]


async def test_filters_combine(client, db):
    await seed(db)

    response = await client.get("/listings/", params={"q": "a", "rooms_min": 2, "price_max": 700_000})

    assert ids(response) == ["Kraków"]


async def test_pagination(client, db):
    await seed(db)

    assert ids(await client.get("/listings/", params={"skip": 1, "limit": 1})) == ["Kraków"]


async def test_invalid_params_return_422(client):
    assert (await client.get("/listings/", params={"limit": 501})).status_code == 422
    assert (await client.get("/listings/", params={"skip": -1})).status_code == 422
    assert (await client.get("/listings/", params={"price_min": 10, "price_max": 5})).status_code == 422
    assert (await client.get("/listings/", params={"area_min": 10, "area_max": 5})).status_code == 422
