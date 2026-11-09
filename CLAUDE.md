# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Monorepo for a Polish real-estate listings app. Each deployable part is a self-contained service under `services/` with its own deps, config, tests and README; services talk only over HTTP and must not import each other's code. Docs, user stories, script output and code comments are largely in Polish — write plans and commit descriptions in the language of the brief.

- `services/backend/` — async FastAPI + SQLAlchemy 2.0 (aiosqlite) + Alembic, Python ≥ 3.11. Has its own `CLAUDE.md` and `.claude/` (hooks, `.env` read-deny) — read `services/backend/CLAUDE.md` before backend work. Note: it predates auth; `main.py` now also has `/auth/register`, `/auth/login` (OAuth2 form, JWT via `sql_app/security.py`), `/auth/me`, and Location write endpoints require a bearer token.
- `services/frontend/` — React 19 + Vite 7, plain JSX, no test runner and no linter. `src/api.js` is the only API client.
- `services/e2e/` — pytest + pytest-playwright (Python) browser tests.

## Commands

From the repo root:

```bash
./install.sh [--with-e2e]   # backend venv + `pip install -e ".[dev]"`, generates services/backend/.env with random SECRET_KEY, runs migrations, npm ci; optionally e2e venv + Chromium
./start.sh                  # migrate DB, then backend on :8000 and Vite on :5173 (override with BACKEND_PORT / FRONTEND_PORT)
```

Per service (run from the service directory):

```bash
# services/backend (venv/ inside the service)
source venv/bin/activate
pytest -q
pytest tests/api/test_locations.py::test_name -q     # single test
alembic revision --autogenerate -m "msg"              # after editing sql_app/models.py

# services/frontend
npm run dev        # dev server; proxies /api/* -> BACKEND_URL (default http://127.0.0.1:8000), stripping the /api prefix
npm run build      # the only "gate" for frontend changes

# services/e2e (its own venv/, needs backend venv + frontend node_modules)
source venv/bin/activate
pytest -q
pytest tests/test_auth.py -q --headed               # single file, visible browser
```

## Cross-service architecture

- **No CORS on the backend.** The browser always calls `/api/...`; Vite's dev proxy rewrites to the backend. Any new frontend call goes through `request()` in `src/api.js`, which attaches the JWT from `localStorage` (`accessToken`) and, on a 401, clears it and dispatches the `auth:expired` window event that `App.jsx` listens for. Login posts form-encoded `username`/`password` (OAuth2PasswordRequestForm), not JSON.
- **E2E spins up the whole stack itself** (`services/e2e/tests/conftest.py`): runs `alembic upgrade head` against a temp SQLite file, starts uvicorn on 8001 using the backend's venv python, and Vite on 5174 with `BACKEND_URL` pointed at it. Set `E2E_BASE_URL` to test an already-running deployment instead. Fixtures `api` (httpx through the `/api` proxy), `user` (fresh unique email) and `auth_headers` seed data without the UI.
- **Two schema paths.** Backend unit tests build tables with `Base.metadata.create_all` (in-memory SQLite, `SECRET_KEY` set in `tests/conftest.py`), so they will pass even if a migration is missing; only the app, `start.sh` and e2e go through Alembic. A model change therefore always needs a migration in the same commit.
- **`docs/schema.md` is generated** from `sql_app/models.py` by `services/backend/scripts/gen_model_docs.py` — don't edit it by hand. The backend's PostToolUse hook regenerates it automatically when models.py is edited (only when Claude Code is started from `services/backend/`). The backend's Stop hook runs `pytest -q` and blocks the turn on red tests.

## CI and review tooling

- `.github/workflows/tests.yml` — backend `pytest -q` on Python 3.11 for every push/PR. Frontend and e2e are not run in CI.
- `.github/workflows/agent-review.yml` — Codex CLI PR review driven by `.agent/review-prompt.md` / `review-schema.json` / `post-review-comment.js`; it flags missing Alembic migrations, API-contract breaks, bad queries and security issues.
- `.claude/agents/commit-planner.md` — subagent that writes Multi-Commit Plans to `.agent/plans/<slug>.md` (see `.agent/plans/listings.md` for an example). Its rules reflect the repo's commit conventions: Conventional Commits with the service as scope (`feat(backend): ...`, `docs: ...`), one service and one reason per commit, tests in the same commit as the behavior, ~5 files / ~200 lines per commit, order schemas → backend → frontend → e2e → docs; new list endpoints use `response_model`, `skip`/`limit` via `Query` with bounds, `selectinload` for relations (lazy loading raises `MissingGreenlet` in async sessions) and deterministic `order_by`.
