#!/usr/bin/env bash
# Instalacja projektu: backend (venv + zależności + baza), frontend (npm) i opcjonalnie testy E2E.
# Użycie: ./install.sh [--with-e2e]
#   --with-e2e  dodatkowo instaluje zależności testów E2E (pytest + Playwright + Chromium)

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
            echo "Użycie: ./install.sh [--with-e2e]"
            exit 0
            ;;
        *)
            echo "❌ Nieznana opcja: $arg"
            exit 1
            ;;
    esac
done

info()  { echo "▶ $*"; }
ok()    { echo "✅ $*"; }
fail()  { echo "❌ $*" >&2; exit 1; }

# --- 1. Sprawdzenie wymaganych narzędzi -------------------------------------
info "Sprawdzanie wymaganych narzędzi..."

command -v python3 >/dev/null 2>&1 || fail "Nie znaleziono python3 (wymagany Python 3.11+)."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || fail "Wymagany Python 3.11+, a masz $(python3 --version 2>&1)."

command -v node >/dev/null 2>&1 || fail "Nie znaleziono node (wymagany Node.js 18+)."
command -v npm  >/dev/null 2>&1 || fail "Nie znaleziono npm."

ok "Python $(python3 --version 2>&1 | cut -d' ' -f2), Node $(node --version), npm $(npm --version)"

# --- 2. Backend --------------------------------------------------------------
info "Backend: środowisko wirtualne i zależności..."
cd "$BACKEND_DIR"

if [ ! -d venv ]; then
    python3 -m venv venv
    ok "Utworzono venv/."
else
    ok "venv/ już istnieje."
fi

# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[dev]"
ok "Zainstalowano zależności backendu (wraz z narzędziami testowymi)."

# Plik .env: SECRET_KEY jest wymagany, więc generujemy losowy klucz.
if [ ! -f .env ]; then
    SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    sed "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|" .env.example > .env
    ok "Utworzono .env z wygenerowanym SECRET_KEY."
else
    ok ".env już istnieje - pozostawiam bez zmian."
fi

info "Backend: inicjalizacja bazy danych (migracje Alembic)..."
python -m sql_app.init_db
deactivate

# --- 3. Frontend -------------------------------------------------------------
info "Frontend: instalacja pakietów npm..."
cd "$FRONTEND_DIR"
if [ -f package-lock.json ]; then
    npm ci
else
    npm install
fi
ok "Zainstalowano zależności frontendu."

# --- 4. E2E (opcjonalnie) ----------------------------------------------------
if [ "$WITH_E2E" -eq 1 ]; then
    info "Testy E2E: środowisko wirtualne, Playwright i Chromium..."
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
    ok "Testy E2E gotowe (uruchomienie: services/e2e -> pytest -q)."
fi

echo ""
echo "🎉 Instalacja zakończona. Uruchom projekt poleceniem: ./start.sh"
