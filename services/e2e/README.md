# programming_tools_ai — e2e tests

End-to-end tests for the whole application (`services/frontend` + `services/backend`), written with **pytest** and **Playwright for Python**. They drive the UI in a real Chromium browser.

## Requirements

- Python 3.11+
- Node.js 20.19+ (or 22+) — the frontend is started with Vite

## Setup

```bash
cd services/e2e
./setup.sh                 # venv, Python deps, Chromium for Playwright, frontend npm install
source venv/bin/activate
```

## Run

```bash
pytest -q                  # all tests, headless Chromium
pytest -q --headed         # watch the browser
pytest -q -k "login"       # subset
pytest --tracing retain-on-failure   # keep a Playwright trace for failed tests
```

By default the suite starts its own servers:

1. the backend (`uvicorn main:app`) on `E2E_BACKEND_PORT` (default `8001`), using a fresh SQLite database in a temporary directory, migrated with `alembic upgrade head`;
2. the frontend (Vite dev server) on `E2E_FRONTEND_PORT` (default `5174`), proxying `/api` to that backend.

Nothing touches `services/backend/sql_app.db`, and each run starts with an empty database.

### Testing an already running application

Set `E2E_BASE_URL` to the frontend address and no servers are started. Requests to the API go through `{E2E_BASE_URL}/api`, the same proxy the frontend uses:

```bash
E2E_BASE_URL=http://127.0.0.1:5173 pytest -q
```

Use this only against a disposable environment: the tests create users and locations.

## Structure

```
services/e2e/
├── tests/
│   ├── conftest.py        # starts backend + frontend, `api` client, `user`, `logged_in_page` fixtures
│   ├── test_auth.py       # register, login, wrong password, logout
│   └── test_locations.py  # add, validation, search, delete, reload
├── pytest.ini
├── requirements.txt
├── setup.sh
└── README.md
```

Each test gets its own browser context (the `page` fixture from `pytest-playwright`), so the login token in `localStorage` never leaks between tests. Users are created with unique emails and cities with unique names, because the locations table is shared by all tests in a session.

## Conventions

- Tests use the UI through accessible locators (`get_by_label`, `get_by_role`, `get_by_placeholder`). Keep them that way and avoid CSS class selectors unless there is no alternative.
- Seed data through the API (`api` fixture) when the test is not about creating it. Keep UI flows for the behaviour under test.
- Test names and UI strings are in Polish, matching the application.
