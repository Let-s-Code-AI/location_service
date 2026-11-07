"""Logowanie, rejestracja i wylogowanie przez interfejs."""

import uuid

from playwright.sync_api import Page, expect


def login_through_ui(page: Page, email: str, password: str):
    page.goto("/")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Hasło").fill(password)
    page.get_by_role("button", name="Zaloguj", exact=True).click()


def test_user_can_register_from_the_ui(page: Page):
    email = f"e2e-{uuid.uuid4().hex[:10]}@example.com"

    page.goto("/")
    page.get_by_role("button", name="Nie mam konta").click()
    expect(page.get_by_role("heading", name="Rejestracja")).to_be_visible()

    page.get_by_label("Email").fill(email)
    page.get_by_label("Hasło").fill("haslo-e2e-123")
    page.get_by_role("button", name="Zarejestruj się").click()

    # Po rejestracji aplikacja loguje użytkownika od razu i pokazuje listę.
    expect(page.get_by_role("heading", name="Lokalizacje", level=1)).to_be_visible()


def test_wrong_password_shows_error(page: Page, user):
    login_through_ui(page, user["email"], "zle-haslo-123")

    alert = page.get_by_role("alert")
    expect(alert).to_contain_text("Nie udało się zalogować")
    expect(alert).to_contain_text("Invalid credentials")
    expect(page.get_by_role("heading", name="Logowanie")).to_be_visible()


def test_valid_login_opens_locations_page(page: Page, user):
    login_through_ui(page, user["email"], user["password"])

    expect(page.get_by_role("heading", name="Lokalizacje", level=1)).to_be_visible()


def test_logout_returns_to_login_form(page: Page, user):
    login_through_ui(page, user["email"], user["password"])
    expect(page.get_by_role("heading", name="Lokalizacje", level=1)).to_be_visible()

    page.get_by_role("button", name="Wyloguj").click()

    expect(page.get_by_role("heading", name="Logowanie")).to_be_visible()
