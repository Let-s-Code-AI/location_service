"""Fixtures E2E: podnosi backend (FastAPI, świeża baza SQLite) i frontend (Vite dev server).

Domyślnie testy same uruchamiają oba serwisy. Jeśli chcesz testować już działającą
aplikację (np. na stagingu), ustaw `E2E_BASE_URL` — wtedy nic nie jest uruchamiane,
a testy idą przez `{E2E_BASE_URL}/api` (ten sam proxy co w dev serwerze Vite).
"""

import os
import shutil
import signal
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import pytest

# tests/conftest.py -> services/e2e/tests -> services/
SERVICES_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = SERVICES_DIR / "backend"
FRONTEND_DIR = SERVICES_DIR / "frontend"

BACKEND_PORT = int(os.environ.get("E2E_BACKEND_PORT", "8001"))
FRONTEND_PORT = int(os.environ.get("E2E_FRONTEND_PORT", "5174"))
SECRET_KEY = "e2e-secret-do-not-use-in-production"


def _backend_python() -> str:
    """Python z venv backendu (ma FastAPI i zależności); fallback na bieżący interpreter."""
    venv_python = BACKEND_DIR / "venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else "python3"


def _wait_until_ready(url: str, process: subprocess.Popen, name: str, log: Path, timeout: float = 60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{name} zakończył się kodem {process.returncode}, log: {log}")
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"{name} nie odpowiedział pod {url} w {timeout}s, log: {log}")


def _stop(process: subprocess.Popen):
    if process.poll() is None:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()


@pytest.fixture(scope="session")
def app_base_url(tmp_path_factory):
    """Bazowy URL frontendu. Uruchamia backend i frontend, chyba że podano E2E_BASE_URL."""
    external = os.environ.get("E2E_BASE_URL")
    if external:
        yield external.rstrip("/")
        return

    if not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError("Brak node_modules — uruchom `npm install` w services/frontend")

    workdir = tmp_path_factory.mktemp("e2e")
    db_file = workdir / "e2e.db"
    env = {
        **os.environ,
        "SECRET_KEY": SECRET_KEY,
        "DATABASE_URL": f"sqlite+aiosqlite:///{db_file}",
    }

    # 1. Schemat bazy — te same migracje co w produkcji (Alembic).
    subprocess.run(
        [_backend_python(), "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
        capture_output=True,
    )

    # 2. Backend.
    backend_log = workdir / "backend.log"
    with backend_log.open("w") as log:
        backend = subprocess.Popen(
            [_backend_python(), "-m", "uvicorn", "main:app", "--port", str(BACKEND_PORT)],
            cwd=BACKEND_DIR,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    # 3. Frontend (Vite proxuje /api do BACKEND_URL).
    frontend_log = workdir / "frontend.log"
    npm = shutil.which("npm") or "npm"
    with frontend_log.open("w") as log:
        frontend = subprocess.Popen(
            [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(FRONTEND_PORT), "--strictPort"],
            cwd=FRONTEND_DIR,
            env={**os.environ, "BACKEND_URL": f"http://127.0.0.1:{BACKEND_PORT}"},
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    base_url = f"http://127.0.0.1:{FRONTEND_PORT}"
    try:
        _wait_until_ready(f"http://127.0.0.1:{BACKEND_PORT}/", backend, "backend", backend_log)
        _wait_until_ready(base_url, frontend, "frontend", frontend_log)
        yield base_url
    finally:
        _stop(frontend)
        _stop(backend)


@pytest.fixture(scope="session")
def base_url(app_base_url):
    # pytest-playwright czyta tę fixture i używa jej przy page.goto("/").
    return app_base_url


@pytest.fixture(scope="session")
def api(app_base_url):
    """Klient HTTP do API przez proxy frontendu (dane testowe bez UI)."""
    with httpx.Client(base_url=f"{app_base_url}/api", timeout=10) as client:
        yield client


@pytest.fixture
def user(api):
    """Świeżo zarejestrowany użytkownik (unikalny email w każdym teście)."""
    credentials = {"email": f"e2e-{uuid.uuid4().hex[:10]}@example.com", "password": "haslo-e2e-123"}
    response = api.post("/auth/register", json=credentials)
    assert response.status_code == 201, response.text
    return credentials


@pytest.fixture
def auth_headers(api, user):
    response = api.post(
        "/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def logged_in_page(page, user):
    """Strona po zalogowaniu na świeżo zarejestrowanego użytkownika (widok lokalizacji)."""
    page.goto("/")
    page.get_by_label("Email").fill(user["email"])
    page.get_by_label("Hasło").fill(user["password"])
    page.get_by_role("button", name="Zaloguj", exact=True).click()
    page.get_by_role("heading", name="Lokalizacje", level=1).wait_for()
    return page
