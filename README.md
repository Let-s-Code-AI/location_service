# programming_tools_ai

A real-estate listings API built with **FastAPI**, **SQLAlchemy (async)** and **SQLite**, with schema migrations managed by **Alembic**.

> **Status:** early development. Only the `Location` resource has full CRUD endpoints. The remaining models (`Building`, `Owner`, `Features`, `Listing`) are defined in the database layer and Pydantic schemas, but have no API endpoints yet.

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
| `POST` | `/locations/` | Create a location | `200` |
| `GET` | `/locations/` | List locations (`skip`, `limit` query params; defaults `0` and `100`) | `200` |
| `GET` | `/locations/{location_id}` | Get a single location | `200`, `404` |
| `PATCH` | `/locations/{location_id}` | Partially update a location (only the supplied fields change) | `200`, `404` |
| `DELETE` | `/locations/{location_id}` | Delete a location | `204`, `404`, `409` |

`DELETE` returns `409 Conflict` when the location is still referenced by one or more listings.

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
.
├── main.py                  # FastAPI app and route handlers
├── config.py                # Settings (pydantic-settings)
├── sql_app/
│   ├── database.py          # Async engine, session factory, get_db dependency
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── init_db.py           # Runs `alembic upgrade head`
│   └── schema.sql           # Reference SQL schema (not used at runtime)
├── alembic/                 # Migration environment and versions
├── alembic.ini
├── setup.sh                 # Virtualenv + dependency installation
├── pyproject.toml
├── .env.example
├── user_stories*.md         # Requirements notes (in Polish)
└── .github/workflows/       # Automated PR review workflow
```

## Automated pull-request review

`.github/workflows/agent-review.yml` runs an AI code review on every pull request. It uses the Codex CLI with the prompt in `.agent/review-prompt.md` and posts the findings as a PR comment. It requires an `OPENAI_API_KEY` repository secret.

## Notes

- `sql_app/database.py` creates the engine with `echo=True`, which logs every SQL statement. Turn it off before deploying to production.
- Local database files (`*.db`) and `.env` are git-ignored.
- No automated test suite is included yet.
