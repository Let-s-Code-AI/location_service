"""GET /listings/suggestions: podpowiedzi miast i dzielnic dla autouzupełniania."""

import pytest

from sql_app import models


async def suggest(client, **params):
    response = await client.get("/listings/suggestions", params=params)
    assert response.status_code == 200, response.text
    return response.json()


async def test_empty_database_returns_empty_list(client):
    assert await suggest(client, field="city") == []


async def test_prefix_match(client, make_listing):
    await make_listing(city="Kraków")
    await make_listing(city="Warszawa")

    assert await suggest(client, field="city", q="Kra") == ["Kraków"]


async def test_prefix_is_case_insensitive_for_ascii(client, make_listing):
    await make_listing(city="Kraków")

    assert await suggest(client, field="city", q="kra") == ["Kraków"]


async def test_values_are_distinct_and_sorted(client, make_listing):
    for city in ("Warszawa", "Kraków", "Kraków", "Gdańsk"):
        await make_listing(city=city)

    assert await suggest(client, field="city") == ["Gdańsk", "Kraków", "Warszawa"]


async def test_null_values_are_skipped(client, make_listing):
    await make_listing(city="Kraków", city_district=None)

    assert await suggest(client, field="city_district") == []


async def test_locations_without_listings_are_skipped(client, db, make_listing):
    await make_listing(city="Kraków")
    db.add(models.Location(city="Poznań"))
    await db.commit()

    assert await suggest(client, field="city") == ["Kraków"]


async def test_district_suggestions_narrowed_by_city(client, make_listing):
    await make_listing(city="Kraków", city_district="Podgórze")
    await make_listing(city="Kraków", city_district="Krowodrza")
    await make_listing(city="Warszawa", city_district="Mokotów")

    assert await suggest(client, field="city_district", city="Kraków") == [
        "Krowodrza",
        "Podgórze",
    ]
    assert await suggest(client, field="city_district") == [
        "Krowodrza",
        "Mokotów",
        "Podgórze",
    ]


async def test_limit(client, make_listing):
    for city in ("Gdańsk", "Kraków", "Warszawa"):
        await make_listing(city=city)

    assert await suggest(client, field="city", limit=1) == ["Gdańsk"]


@pytest.mark.parametrize("q", ["%", "_", "\\"])
async def test_like_wildcards_are_escaped(client, make_listing, q):
    await make_listing(city="Kraków")

    assert await suggest(client, field="city", q=q) == []


async def test_literal_wildcard_still_matches(client, make_listing):
    await make_listing(city="Miasto_1")
    await make_listing(city="MiastoX1")

    assert await suggest(client, field="city", q="Miasto_") == ["Miasto_1"]


@pytest.mark.parametrize(
    "params",
    [
        {"field": "street"},
        {},
        {"field": "city", "limit": 51},
        {"field": "city", "limit": 0},
    ],
)
async def test_invalid_params_return_422(client, params):
    response = await client.get("/listings/suggestions", params=params)

    assert response.status_code == 422, params
