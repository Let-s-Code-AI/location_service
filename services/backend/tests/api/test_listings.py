"""GET /listings/: lista ofert z paginacją i polem total."""


async def test_list_listings_empty(client):
    response = await client.get("/listings/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "skip": 0, "limit": 50}


async def test_list_listings_returns_summary_with_location(client, make_listing):
    listing = await make_listing(
        city="Kraków",
        city_district="Podgórze",
        rooms=3,
        area=62.5,
        price_total_zl=850000.0,
        price_sqm_zl=13600.0,
        url="https://example.com/oferta",
        description_text="Opis",
    )

    body = (await client.get("/listings/")).json()

    assert body["total"] == 1
    assert body["items"] == [
        {
            "listing_id": listing.listing_id,
            "rooms": 3,
            "area": 62.5,
            "price_total_zl": 850000.0,
            "price_sqm_zl": 13600.0,
            "location": {"city": "Kraków", "city_district": "Podgórze"},
        }
    ]


async def test_list_listings_paginates_and_total_ignores_page(client, make_listing):
    created = [await make_listing(rooms=n) for n in (1, 2, 3)]

    body = (await client.get("/listings/", params={"skip": 1, "limit": 1})).json()

    assert body["total"] == 3
    assert body["skip"] == 1 and body["limit"] == 1
    assert [item["listing_id"] for item in body["items"]] == [created[1].listing_id]


async def test_list_listings_is_ordered_by_id(client, make_listing):
    created = [await make_listing() for _ in range(3)]

    body = (await client.get("/listings/")).json()

    assert [item["listing_id"] for item in body["items"]] == [
        listing.listing_id for listing in created
    ]


async def test_list_listings_rejects_invalid_pagination(client):
    for params in ({"limit": 0}, {"limit": 501}, {"skip": -1}):
        response = await client.get("/listings/", params=params)
        assert response.status_code == 422, params
