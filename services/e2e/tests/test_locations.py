"""Zarządzanie lokalizacjami przez interfejs (dodawanie, walidacja, wyszukiwanie, usuwanie)."""

import uuid

from playwright.sync_api import Locator, Page, expect


def unique_city() -> str:
    # Baza jest współdzielona przez wszystkie testy sesji — każdy test używa własnej nazwy.
    return f"E2E-{uuid.uuid4().hex[:8]}"


def row_for(page: Page, city: str) -> Locator:
    return page.locator("tbody tr", has_text=city)


def add_location_through_ui(page: Page, city: str):
    page.get_by_label("Miasto").fill(city)
    page.get_by_role("button", name="Dodaj", exact=True).click()


def test_added_location_appears_in_the_list(logged_in_page: Page):
    page = logged_in_page
    city = unique_city()

    add_location_through_ui(page, city)

    expect(page.get_by_role("status")).to_contain_text("Dodano lokalizację")
    expect(row_for(page, city)).to_be_visible()
    # Formularz po zapisie się czyści.
    expect(page.get_by_label("Miasto")).to_have_value("")


def test_city_is_required(logged_in_page: Page):
    page = logged_in_page

    page.get_by_role("button", name="Dodaj", exact=True).click()

    expect(page.locator(".hint")).to_have_text("Pole „Miasto” jest wymagane.")
    expect(page.get_by_label("Miasto")).to_have_class("invalid")


def test_location_with_street_is_marked_complete(logged_in_page: Page):
    page = logged_in_page
    city = unique_city()

    page.get_by_label("Miasto").fill(city)
    page.get_by_label("Dzielnica").fill("Mokotów")
    page.get_by_label("Ulica").fill("Puławska")
    page.get_by_role("button", name="Dodaj", exact=True).click()

    expect(row_for(page, city).locator(".tag")).to_have_text("Kompletna")


def test_search_filters_the_list(logged_in_page: Page, auth_headers, api):
    page = logged_in_page
    wanted = unique_city()
    other = unique_city()
    api.post("/locations/", json={"city": wanted, "street": "Marszałkowska"}, headers=auth_headers)
    api.post("/locations/", json={"city": other}, headers=auth_headers)
    page.reload()
    expect(row_for(page, wanted)).to_be_visible()

    page.get_by_placeholder("Szukaj…").fill(wanted)

    expect(row_for(page, wanted)).to_be_visible()
    expect(row_for(page, other)).to_have_count(0)


def test_search_without_matches_shows_empty_state(logged_in_page: Page):
    page = logged_in_page

    page.get_by_placeholder("Szukaj…").fill(f"brak-{uuid.uuid4().hex}")

    expect(page.get_by_text("Brak wyników")).to_be_visible()


def test_deleted_location_disappears_from_the_list(logged_in_page: Page, auth_headers, api):
    page = logged_in_page
    city = unique_city()
    api.post("/locations/", json={"city": city}, headers=auth_headers)
    page.reload()
    expect(row_for(page, city)).to_be_visible()

    row_for(page, city).get_by_title("Usuń").click()

    expect(row_for(page, city)).to_have_count(0)
    expect(page.get_by_role("status")).to_contain_text("Usunięto lokalizację")


def test_locations_are_visible_after_reload(logged_in_page: Page, auth_headers, api):
    page = logged_in_page
    city = unique_city()
    api.post("/locations/", json={"city": city}, headers=auth_headers)
    page.reload()
    expect(row_for(page, city)).to_be_visible()

    page.reload()

    expect(row_for(page, city)).to_be_visible()
