"""GET /listings/: filtry zakresów ceny, ceny za m², metrażu oraz pokoi."""
import pytest


async def ids(client, **params):
    response = await client.get("/listings/", params=params)
    assert response.status_code == 200, response.text
    body = response.json()
    return {item["listing_id"] for item in body["items"]}, body["total"]


RANGES = [
    ("price_total", "price_total_zl", (300000.0, 500000.0, 700000.0)),
    ("price_sqm", "price_sqm_zl", (9000.0, 12000.0, 15000.0)),
    ("area", "area", (35.0, 50.0, 80.0)),
]


@pytest.mark.parametrize("param, field, values", RANGES)
async def test_range_filter_min_max_and_both(client, make_listing, param, field, values):
    low, mid, high = [await make_listing(**{field: v}) for v in values]

    assert await ids(client, **{f"{param}_min": values[1]}) == ({mid.listing_id, high.listing_id}, 2)
    assert await ids(client, **{f"{param}_max": values[1]}) == ({low.listing_id, mid.listing_id}, 2)
    assert await ids(
        client, **{f"{param}_min": values[1], f"{param}_max": values[1]}
    ) == ({mid.listing_id}, 1)


@pytest.mark.parametrize("param, field, values", RANGES)
async def test_range_filter_excludes_null_only_when_active(client, make_listing, param, field, values):
    with_value = await make_listing(**{field: values[1]})
    without_value = await make_listing()

    assert await ids(client) == ({with_value.listing_id, without_value.listing_id}, 2)
    assert await ids(client, **{f"{param}_min": 0}) == ({with_value.listing_id}, 1)


async def test_rooms_single_and_multiple(client, make_listing):
    one, two, three = [await make_listing(rooms=n) for n in (1, 2, 3)]
    await make_listing()  # rooms NULL

    assert await ids(client, rooms=2) == ({two.listing_id}, 1)
    assert await ids(client, rooms=[1, 3]) == ({one.listing_id, three.listing_id}, 2)


async def test_combined_filters(client, make_listing):
    match = await make_listing(rooms=2, area=50.0, price_total_zl=500000.0, price_sqm_zl=10000.0)
    await make_listing(rooms=2, area=50.0, price_total_zl=900000.0, price_sqm_zl=18000.0)
    await make_listing(rooms=4, area=50.0, price_total_zl=500000.0, price_sqm_zl=10000.0)

    assert await ids(
        client, rooms=2, area_min=40, price_total_max=600000, price_sqm_max=12000
    ) == ({match.listing_id}, 1)


async def test_total_reflects_filters_not_page(client, make_listing):
    for n in (2, 2, 2, 3):
        await make_listing(rooms=n)

    body = (await client.get("/listings/", params={"rooms": 2, "limit": 1})).json()

    assert body["total"] == 3
    assert len(body["items"]) == 1


@pytest.mark.parametrize("param", ["price_total", "price_sqm", "area"])
async def test_min_greater_than_max_returns_422_with_message(client, param):
    response = await client.get("/listings/", params={f"{param}_min": 10, f"{param}_max": 5})

    assert response.status_code == 422
    assert response.json()["detail"] == f"{param}_min nie może być większe niż {param}_max"


@pytest.mark.parametrize(
    "params",
    [
        {"price_total_min": -1},
        {"price_sqm_max": -1},
        {"area_min": -0.5},
        {"rooms": 0},
        {"rooms": [2, -1]},
        {"price_total_min": "inf"},
        {"area_max": "nan"},
    ],
)
async def test_invalid_filter_values_return_422(client, params):
    response = await client.get("/listings/", params=params)

    assert response.status_code == 422, params
