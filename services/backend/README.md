# programming_tools_ai — backend

This is the backend service (`services/backend/`). Run all commands below from this directory.

A real-estate listings API built with **FastAPI**, **SQLAlchemy (async)** and **SQLite**, with schema migrations managed by **Alembic**.

> **Status:** early development. `Location` has full CRUD endpoints; `Listing` can be listed with filters and a result count (read-only). The remaining models (`Building`, `Owner`, `Features`) are defined in the database layer and Pydantic schemas, but have no API endpoints yet.

## Tech stack

| Area | Tool |
| --- | --- |
| Web framework | FastAPI 0.104 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) with `aiosqlite` |
| Migrations | Alembic |
| Configuration | pydantic-settings |
| Database | SQLite |
| Python | 3.11+ |

## Getting started

### 1. Install

```bash
./setup.sh
```

The script creates a `venv/` virtual environment, upgrades `pip` and installs the project in editable mode (`pip install -e .`). Activate the environment afterwards with:

```bash
source venv/bin/activate
```

### 2. Configure

Copy the example environment file and adjust it if needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./sql_app.db` | Async SQLAlchemy connection URL |
| `SECRET_KEY` | — (required) | Secret used to sign JWT tokens. Generate one, e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Lifetime of access tokens |

Settings are loaded by `config.py` from environment variables or the `.env` file.

### 3. Create the database

Apply all Alembic migrations:

```bash
alembic upgrade head
```

or, equivalently:

```bash
python -m sql_app.init_db
```

Both are safe to run repeatedly; migrations that are already applied are skipped.

### 4. Run the API

```bash
uvicorn main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive documentation is generated automatically:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## API reference

| Method | Path | Description | Responses |
| --- | --- | --- | --- |
| `GET` | `/` | Health check (`{"message": "API is running"}`) | `200` |
| `POST` | `/auth/register` | Register a user (`email`, `password` min. 8 chars) | `201`, `409`, `422` |
| `POST` | `/auth/login` | Log in (form data `username` = email, `password`); returns `access_token` | `200`, `401` |
| `GET` | `/auth/me` | Current user (requires token) | `200`, `401` |
| `POST` | `/locations/` | Create a location (auth required) | `200`, `401` |
| `GET` | `/locations/` | List locations (`skip`, `limit` query params; defaults `0` and `100`) | `200` |
| `GET` | `/locations/{location_id}` | Get a single location | `200`, `404` |
| `PATCH` | `/locations/{location_id}` | Partially update a location (auth required; only the supplied fields change) | `200`, `401`, `404` |
| `DELETE` | `/locations/{location_id}` | Delete a location (auth required) | `204`, `401`, `404`, `409` |
| `GET` | `/listings/` | List listings with filters (see below); returns `{items, total, skip, limit}` | `200`, `422` |
| `GET` | `/listings/suggestions` | Autocomplete for `city` / `city_district` (`field`, `q` prefix, optional `city`, `limit` 1–50, default `10`) | `200`, `422` |

`DELETE` returns `409 Conflict` when the location is still referenced by one or more listings.

### Listing filters

`GET /listings/` is public and accepts `skip` (default `0`), `limit` (default `50`, max `500`) and any combination of:

| Parameter | Meaning |
| --- | --- |
| `q` | Substring of city, locality, district or street (max 100 chars) |
| `price_total_min`, `price_total_max` | Total price in zł (inclusive) |
| `price_sqm_min`, `price_sqm_max` | Price per m² in zł (inclusive) |
| `area_min`, `area_max` | Area in m² (inclusive) |
| `rooms` | Number of rooms; repeat for several values (`rooms=2&rooms=3`) |
| `city`, `city_district` | Exact match on the listing's location |

Ranges must be non-negative and finite, with min ≤ max, otherwise the API returns `422` with a message in `detail`. A listing with an empty (`NULL`) value in a filtered field is excluded only while that filter is active. `total` is the number of listings matching the filters, regardless of `skip`/`limit`. Each item contains `listing_id`, `rooms`, `area`, `price_total_zl`, `price_sqm_zl` and `location` (`city`, `city_district`, `street`).

SQLite `LIKE` is case-insensitive only for ASCII, so `q=łódź` does not match `Łódź`. There is no `POST /listings/` yet. To get sample data locally, run `venv/bin/python scripts/seed_listings.py` (it does nothing when the table is not empty).

`GET /listings/suggestions` returns a sorted list of distinct values that start with `q`, taken only from locations that have at least one listing; with `field=city_district`, `city` narrows the districts to one city. The match is case-insensitive only for ASCII letters (SQLite `LIKE`).

```bash
# 2- and 3-room flats in Kraków between 400k and 700k zł
curl "http://127.0.0.1:8000/listings/?city=Krak%C3%B3w&rooms=2&rooms=3&price_total_min=400000&price_total_max=700000"

# District suggestions in Kraków starting with "Pod"
curl "http://127.0.0.1:8000/listings/suggestions?field=city_district&q=Pod&city=Krak%C3%B3w"
```

### Authentication

Write endpoints for locations require a JWT in the `Authorization: Bearer <token>` header. Get a token from `/auth/login`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email": "jan@example.com", "password": "haslo-12345"}'

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d 'username=jan@example.com&password=haslo-12345' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -X POST http://127.0.0.1:8000/locations/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"city": "Warsaw"}'
```

Passwords are hashed with bcrypt. Tokens are HS256 JWTs valid for `ACCESS_TOKEN_EXPIRE_MINUTES`.

### Example

```bash
# Create a location
curl -X POST http://127.0.0.1:8000/locations/ \
  -H "Content-Type: application/json" \
  -d '{"city": "Warsaw", "street": "Marszalkowska", "latitude": 52.2297, "longitude": 21.0122}'

# List locations with pagination
curl "http://127.0.0.1:8000/locations/?skip=0&limit=10"

# Update a single field
curl -X PATCH http://127.0.0.1:8000/locations/1 \
  -H "Content-Type: application/json" \
  -d '{"city_district": "Srodmiescie"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/locations/1
```

All `Location` fields (`city`, `locality`, `city_district`, `street`, `full_address`, `latitude`, `longitude`) are optional.

## Data model

```
location ──┐
building ──┤
owner    ──┼──< listing
features ──┘
```

Each `listing` references exactly one `location`, `building`, `owner` and `features` row.

| Table | Main columns |
| --- | --- |
| `location` | `city`, `locality`, `city_district`, `street`, `full_address`, `latitude`, `longitude` |
| `building` | `year_built`, `building_type`, `floor` |
| `owner` | `owner_type`, `contact_name`, `contact_phone`, `contact_email` |
| `features` | `has_basement`, `has_parking`, `kitchen_type`, `window_type`, `ownership_type`, `equipment` |
| `listing` | `rooms`, `area`, `price_total_zl`, `price_sqm_zl`, `price_per_sqm_detailed`, `date_posted`, `photo_count`, `url`, `image_url`, `description_text` + foreign keys to the four tables above |

## Database migrations

The schema is owned by Alembic (`alembic/versions/`). After changing `sql_app/models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Alembic uses a synchronous engine, so `alembic/env.py` converts `sqlite+aiosqlite://` to `sqlite://` automatically; you only need to maintain `DATABASE_URL`.

## Project structure

```
services/backend/
├── main.py                  # FastAPI app, route handlers, auth dependency
├── config.py                # Settings (pydantic-settings)
├── sql_app/
│   ├── database.py          # Async engine, session factory, get_db dependency
│   ├── models.py            # SQLAlchemy ORM models
│   ├── security.py          # Password hashing (bcrypt) and JWT helpers
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── init_db.py           # Runs `alembic upgrade head`
│   └── schema.sql           # Reference SQL schema (not used at runtime)
├── scripts/                 # gen_model_docs.py, seed_listings.py
├── alembic/                 # Migration environment and versions
├── alembic.ini
├── setup.sh                 # Virtualenv + dependency installation
├── pyproject.toml
├── .env.example
└── .claude/                 # Claude Code settings
```

## Automated pull-request review

`.github/workflows/agent-review.yml` (repo root) runs an AI code review on every pull request. It uses the Codex CLI with the prompt in `.agent/review-prompt.md` and posts the findings as a PR comment. It requires an `OPENAI_API_KEY` repository secret.

## Notes

- `sql_app/database.py` creates the engine with `echo=True`, which logs every SQL statement. Turn it off before deploying to production.
- Local database files (`*.db`) and `.env` are git-ignored.
- Tests live in `tests/` and run with `pytest -q` (in-memory SQLite).
