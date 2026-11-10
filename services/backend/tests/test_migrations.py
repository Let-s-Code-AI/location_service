"""Alembic migrations vs. ORM models.

The API tests build the schema with ``Base.metadata.create_all`` and never run
Alembic, so a model change without a migration, or an ``env.py`` that no longer
registers the models, would otherwise surface only in E2E tests or at runtime.

Alembic runs in a subprocess on purpose: this test process has already imported
``sql_app.models`` (see conftest), so running Alembic in-process would mask an
``env.py`` that no longer imports the models itself.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic(*args, db_path):
    """Run the Alembic CLI from the backend root, the same way a developer does."""
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_migrations_match_models(tmp_path):
    """``alembic upgrade head`` on an empty DB yields exactly the schema the models describe.

    ``alembic check`` fails when autogenerate would emit any operation, which
    covers both a model change without a migration and an ``env.py`` that stops
    importing ``sql_app.models`` (autogenerate then drops every table).
    """
    db_path = tmp_path / "migrated.db"

    upgrade = alembic("upgrade", "head", db_path=db_path)
    assert upgrade.returncode == 0, upgrade.stderr

    check = alembic("check", db_path=db_path)
    assert check.returncode == 0, (
        f"Migrations and models disagree:\n{check.stdout}{check.stderr}"
    )
