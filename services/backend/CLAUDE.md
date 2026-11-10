# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Backend service (`services/backend/`) of a Polish real-estate listings app: async FastAPI + SQLAlchemy 2.0 (aiosqlite) REST API. The frontend lives separately in `services/frontend/`. Python >= 3.11. Project docs (`user_stories*.md`, in the repo root) are in Polish. New code comments must be in English (see the repo-root `CLAUDE.md`), but many existing ones are still in Polish. Tests live in `tests/` (pytest). ruff is the linter and formatter (`[tool.ruff]` in `pyproject.toml`; `alembic/versions` is excluded).

## Commands

```bash
./setup.sh                       # create venv/, install deps via `pip install -e .` (deps are pinned in pyproject.toml)
source venv/bin/activate
python -m sql_app.init_db        # create/upgrade DB: runs `alembic upgrade head`
uvicorn main:app --reload        # run the API (docs at /docs)
pip install -e ".[dev]"          # dev deps: pytest, pytest-asyncio, pytest-cov, httpx, ruff, diff-cover
pytest -q                        # run tests (in-memory SQLite, see tests/conftest.py)
ruff check --fix . && ruff format .   # lint + format; CI rejects unformatted code
./scripts/quality.sh             # the CI gate: ruff check, ruff format --check, pytest --cov (fail_under = 80); writes coverage.xml
diff-cover coverage.xml --compare-branch=origin/main --fail-under=90   # coverage of lines changed vs main (also run in CI)

alembic revision --autogenerate -m "message"   # generate a migration after changing sql_app/models.py
alembic upgrade head
alembic downgrade -1
```

Run these from `services/backend/` — `alembic.ini` and the default SQLite URL (`./sql_app.db`) are relative to it.

## Architecture

- `main.py` — the whole HTTP layer: a single `FastAPI` app with route handlers written directly against `AsyncSession` (no router/service/repository layers). `Location` has CRUD endpoints (`/locations/`, PATCH for partial update, DELETE returns 409 if listings reference the location). `Listing` is read-only: `GET /listings/` returns a `ListingPage` envelope (`items` as `ListingSummary` with nested `location` loaded via `selectinload` — required, because lazy loading raises `MissingGreenlet` in an async session; `total` counted with the same filters, independent of `skip`/`limit`); filters come from the `listing_filters` dependency (free-text `q` matched as a substring of city/locality/district/street, price/price per m²/area ranges, repeated `rooms`, exact `city`/`city_district`; min > max or non-finite values → 422 with a string `detail`). `GET /listings/suggestions?field=city|city_district&q=&city=` returns distinct prefix matches from locations that have listings; it must stay declared before any future `/listings/{listing_id}`. `Building`, `Owner` and `Features` have models and schemas but no endpoints. `scripts/seed_listings.py` fills an empty `listing` table with sample data for manual testing.
- `sql_app/database.py` — async engine (`echo=True`), `AsyncSessionLocal` (`expire_on_commit=False`), declarative `Base`, and the `get_db` FastAPI dependency.
- `sql_app/models.py` — SQLAlchemy models. `Listing` is the central table with non-null FKs to `location`, `building`, `owner` and `features`.
- `sql_app/schemas.py` — Pydantic v2 schemas following a `XBase` / `XCreate` / `X` (with `from_attributes=True`) pattern; `ListingDetail` embeds the related objects. `LocationUpdate` makes every field optional and handlers apply it with `model_dump(exclude_unset=True)` for PATCH semantics.
- `config.py` — `pydantic-settings` `Settings` (`database_url`, overridable via env or `.env`; see `.env.example`). Imported by both `sql_app/database.py` and `alembic/env.py`.

### Database schema management

Alembic is the source of truth for the schema (`alembic/versions/`). `sql_app/init_db.py` just calls `alembic upgrade head` — it does not use `Base.metadata.create_all`. `sql_app/schema.sql` is a raw-SQL reference copy of the original schema and is not executed by anything; keep it in mind if models change, but migrations are what actually apply.

`alembic/env.py` takes the URL from `config.settings` and rewrites `sqlite+aiosqlite` → `sqlite`, because migrations run on a **sync** engine while the app uses the async driver. It also sets `render_as_batch=True` (needed for SQLite `ALTER TABLE`), and imports `sql_app.models` so autogenerate sees all tables — new models must be importable via that module.

## CI

`.github/workflows/quality.yml` (in the repo root) runs `scripts/quality.sh` and `diff-cover --fail-under=90` on every pull request that touches `services/backend/`, then uploads `coverage.xml` to Codecov under the `backend` flag; see the Commands section above for what that includes.

`.github/workflows/agent-review.yml` (in the repo root) runs an automated PR review with OpenAI Codex CLI using the repo-root `.agent/review-prompt.md`, `.agent/review-schema.json` and `.agent/post-review-comment.js`. The review prompt specifically looks for missing Alembic migrations, API-contract breaks, and bad queries, so model changes should ship with a migration.
