"""E2E: wyszukiwarka ofert (widok „Oferty”).

Backend nie ma POST /listings/, więc dane wstawiamy bezpośrednio do bazy SQLite
backendu E2E. Każdy test używa unikalnej nazwy miasta, bo baza jest wspólna dla sesji.
"""

import sqlite3
import uuid

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def add_listing(app_base_url, e2e_db_file):
    if e2e_db_file is None:
        pytest.skip("Brak dostępu do bazy przy E2E_BASE_URL — nie da się wstawić ogłoszeń")

    def _add(city: str, street: str, price: float, rooms: int = 2, area: float = 50.0) -> None:
        with sqlite3.connect(e2e_db_file) as conn:
            location_id = conn.execute(
                "INSERT INTO location (city, street) VALUES (?, ?)", (city, street)
            ).lastrowid
            building_id = conn.execute("INSERT INTO building DEFAULT VALUES").lastrowid
            owner_id = conn.execute("INSERT INTO owner DEFAULT VALUES").lastrowid
            features_id = conn.execute("INSERT INTO features DEFAULT VALUES").lastrowid
            conn.execute(
                "INSERT INTO listing (location_id, building_id, owner_id, features_id,"
                " price_total_zl, rooms, area) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (location_id, building_id, owner_id, features_id, price, rooms, area),
            )

    return _add


def open_listings(page: Page) -> Page:
    page.get_by_role("button", name="Oferty").click()
    page.get_by_role("heading", name="Oferty", level=1).wait_for()
    return page


def rows(page: Page):
    return page.locator("tbody tr")


def test_search_by_city_filters_results(logged_in_page: Page, add_listing):
    city = f"Miasto-{uuid.uuid4().hex[:8]}"
    add_listing(city, "Lipowa", 500_000)
    add_listing(city, "Klonowa", 700_000)
    add_listing(f"Inne-{uuid.uuid4().hex[:8]}", "Lipowa", 600_000)
    page = open_listings(logged_in_page)

    page.get_by_label("Szukaj ofert").fill(city)

    expect(rows(page)).to_have_count(2)
    expect(rows(page).first).to_contain_text(city)
    expect(page.get_by_text("2 oferty", exact=True)).to_be_visible()


def test_search_without_matches_shows_empty_state(logged_in_page: Page, add_listing):
    add_listing(f"Miasto-{uuid.uuid4().hex[:8]}", "Lipowa", 500_000)
    page = open_listings(logged_in_page)

    page.get_by_label("Szukaj ofert").fill(f"brak-{uuid.uuid4().hex}")

    expect(page.get_by_text("Brak ofert")).to_be_visible()


def test_max_price_narrows_results_and_clear_resets(logged_in_page: Page, add_listing):
    city = f"Miasto-{uuid.uuid4().hex[:8]}"
    add_listing(city, "Tania", 400_000)
    add_listing(city, "Droga", 900_000)
    page = open_listings(logged_in_page)
    page.get_by_label("Szukaj ofert").fill(city)
    expect(rows(page)).to_have_count(2)

    page.get_by_label("Cena (zł) do").fill("500000")

    expect(rows(page)).to_have_count(1)
    expect(rows(page).first).to_contain_text("Tania")

    page.get_by_role("button", name="Wyczyść filtry").click()

    expect(page.get_by_label("Szukaj ofert")).to_have_value("")
    expect(page.get_by_label("Cena (zł) do")).to_have_value("")
