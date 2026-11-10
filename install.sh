#!/usr/bin/env bash
# Project installation: backend (venv + dependencies + database), frontend (npm), and optional E2E tests.
# Usage: ./install.sh [--with-e2e]
#   --with-e2e  additionally installs E2E test dependencies (pytest + Playwright + Chromium)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/services/backend"
FRONTEND_DIR="$ROOT_DIR/services/frontend"
E2E_DIR="$ROOT_DIR/services/e2e"

WITH_E2E=0
for arg in "$@"; do
    case "$arg" in
        --with-e2e) WITH_E2E=1 ;;
        -h|--help)
            echo "Usage: ./install.sh [--with-e2e]"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $arg"
            exit 1
            ;;
    esac
done

info()  { echo "▶ $*"; }
ok()    { echo "✅ $*"; }
fail()  { echo "❌ $*" >&2; exit 1; }

# --- 1. Checking required tools -----------------------------------------------
info "Checking required tools..."

command -v python3 >/dev/null 2>&1 || fail "python3 not found (Python 3.11+ required)."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || fail "Python 3.11+ required, you have $(python3 --version 2>&1)."

command -v node >/dev/null 2>&1 || fail "node not found (Node.js 18+ required)."
command -v npm  >/dev/null 2>&1 || fail "npm not found."

ok "Python $(python3 --version 2>&1 | cut -d' ' -f2), Node $(node --version), npm $(npm --version)"

# --- 2. Backend --------------------------------------------------------------
info "Backend: virtual environment and dependencies..."
cd "$BACKEND_DIR"

if [ ! -d venv ]; then
    python3 -m venv venv
    ok "Created venv/."
else
    ok "venv/ already exists."
fi

# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[dev]"
ok "Backend dependencies installed (including test tools)."

# .env file: SECRET_KEY is required, so generate a random key.
if [ ! -f .env ]; then
    SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    sed "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|" .env.example > .env
    ok "Created .env with generated SECRET_KEY."
else
    ok ".env already exists - leaving unchanged."
fi

info "Backend: database initialization (Alembic migrations)..."
python -m sql_app.init_db
deactivate

# --- 3. Frontend -------------------------------------------------------------
info "Frontend: installing npm packages..."
cd "$FRONTEND_DIR"
if [ -f package-lock.json ]; then
    npm ci
else
    npm install
fi
ok "Frontend dependencies installed."

# --- 4. E2E (optional) -------------------------------------------------------
if [ "$WITH_E2E" -eq 1 ]; then
    info "E2E tests: virtual environment, Playwright and Chromium..."
    cd "$E2E_DIR"
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    # shellcheck disable=SC1091
    source venv/bin/activate
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r requirements.txt
    python -m playwright install chromium
    deactivate
    ok "E2E tests ready (run: services/e2e -> pytest -q)."
fi

echo ""
echo "🎉 Installation complete. Run the project with: ./start.sh"
