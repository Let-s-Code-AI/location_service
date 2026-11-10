# programming_tools_ai

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Monorepo for a Polish real-estate listings app. Three self-contained services under `services/`, which talk to each other only over HTTP and never import code from one another:

- `services/backend` — async FastAPI + SQLAlchemy 2.0 (aiosqlite) + Alembic, Python 3.11+. It has its own `CLAUDE.md`, which covers its architecture in detail; read it before changing backend code.
- `services/frontend` — React 19 + Vite 7, plain JavaScript. Tests run with Vitest + Testing Library (`npm test`; `npm run test:coverage` enforces the thresholds in `vite.config.js`). ESLint flat config lives in `eslint.config.js` (`npm run lint`).
- `services/e2e` — pytest + Playwright (Python), which drives the real UI in Chromium.

Requirements docs (`docs/user_stories.md`, `docs/models.md`, `docs/database.md`), UI strings, test names and the shell scripts are mostly in Polish. Match that language when you edit them. Code comments are the exception — see below.

## Commands

```bash
./install.sh [--with-e2e]   # backend venv + `pip install -e ".[dev]"`, generates .env with SECRET_KEY, migrates DB, npm ci for frontend
./start.sh                  # migrate DB, then backend :8000 + frontend :5173 (override with BACKEND_PORT / FRONTEND_PORT)

# backend (run from services/backend, venv activated)
pytest -q
pytest tests/api/test_locations.py::test_name -q
ruff check --fix . && ruff format .   # lint + format (config in pyproject.toml)
./scripts/quality.sh                  # what CI runs: ruff check, ruff format --check, pytest --cov (fail_under); writes coverage.xml
alembic revision --autogenerate -m "msg" && alembic upgrade head

# frontend (services/frontend)
npm run dev | npm run build | npm test
npm run lint | npm run test:coverage  # what CI runs (plus npm run build)

# e2e (services/e2e, own venv via ./setup.sh)
pytest -q [--headed] [-k login]
E2E_BASE_URL=http://127.0.0.1:5173 pytest -q   # test an already-running app instead of spawning servers
```

CI (`.github/workflows/quality.yml`, pull requests only) is a per-service quality gate. A `changes` job (`dorny/paths-filter`) runs the `backend` job only when `services/backend/**` changed and the `frontend` job only when `services/frontend/**` changed; editing the workflow itself runs both. Backend: `scripts/quality.sh` (ruff check, ruff format --check, `pytest --cov` with `fail_under = 80` from `pyproject.toml`), then `diff-cover coverage.xml --compare-branch=origin/main --fail-under=90`, so lines added or changed in a PR need 90% coverage even though the whole-project floor is lower. Frontend: `npm ci`, `npm run lint`, `npm run test:coverage` (thresholds in `vite.config.js`), `npm run build`. E2E tests do not run in CI.

## Cross-service architecture

- **Frontend → backend via the `/api` proxy.** The backend has no CORS configuration, so `vite.config.js` proxies `/api/*` to `BACKEND_URL` (default `http://127.0.0.1:8000`) and strips the prefix. All calls go through `src/api.js`. The JWT is kept in `localStorage` (`accessToken`), and when the backend rejects a token, `api.js` dispatches an `auth:expired` event that `App.jsx` listens for.
- **Auth.** Write endpoints require `Authorization: Bearer <JWT>`. Tokens come from `POST /auth/login`, which takes form data with `username` set to the email. The backend won't start without `SECRET_KEY` (a required `Settings` field). The backend test conftest sets it before importing `main`, and the E2E conftest passes it in the uvicorn subprocess env.
- **The two test setups build the schema differently.** Backend unit tests (`services/backend/tests/conftest.py`) use in-memory SQLite with `Base.metadata.create_all` and override `get_db`, so they **do not exercise Alembic migrations**. The E2E conftest starts uvicorn from the backend venv on port 8001, using a fresh temp SQLite DB migrated with `alembic upgrade head`, plus Vite on port 5174. A missing migration therefore surfaces only in E2E or at runtime.
- **API contract changes span services.** A change to a backend schema or endpoint usually needs matching changes in `services/frontend/src/api.js` and the UI, and possibly in the e2e tests. E2E tests use accessible locators (`get_by_label`/`get_by_role`/`get_by_placeholder`), not CSS classes, so changing a label breaks them.

## Conventions and tooling

- Every change to `sql_app/models.py` ships with an Alembic migration in the same commit. The automated PR review (`.github/workflows/agent-review.yml`, Codex CLI driven by `.agent/review-prompt.md`, needs the `OPENAI_API_KEY` secret) flags missing migrations, API-contract breaks and bad queries.
- Backend lint and formatting are ruff (`[tool.ruff]` in `pyproject.toml`: rules `E4 E7 E9 F I B UP`, `alembic/versions` excluded, FastAPI `Depends`/`Query` allowed in argument defaults). Run `ruff check --fix . && ruff format .` before committing; CI fails on unformatted code. The frontend uses ESLint with the Vite React preset; `react-hooks/set-state-in-effect` is only a warning because the existing data-fetching effects trigger it.
- `docs/schema.md` is **generated** by `services/backend/scripts/gen_model_docs.py`. Do not edit it by hand. The backend's `.claude/settings.json` has a PostToolUse hook that regenerates it after any write to `models.py`, plus a Stop hook that runs `pytest -q` and blocks the turn on failures. These hooks are active only when Claude Code is started from `services/backend`.
- Commits follow Conventional Commits with the service as the scope (`feat(backend): ...`, `docs: ...`). The `commit-planner` subagent (`.claude/agents/commit-planner.md`) writes multi-commit plans to `.agent/plans/<slug>.md` using the rules there: one cause and one service per commit, tests in the same commit as the behavior, at most about 5 files / 200 lines, and the order contract → backend → frontend → e2e → docs.
- Another session may auto-commit the working tree while you work. Check `git log` and `git status` before overwriting files.

## Code comments

- Write all code comments in **English**: inline comments, docstrings, and file headers, in every service (backend, frontend, e2e).
- Many existing comments are still in Polish. Translate a comment to English only when you change the code it describes; don't rewrite comments in unrelated code.
- This rule covers comments only. User-facing UI text, API error messages (`detail`), test names, and requirement docs (`user_stories*.md`, `.agent/plans/`) stay in their current language.
