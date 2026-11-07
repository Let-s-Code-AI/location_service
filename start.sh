#!/usr/bin/env bash
# Uruchamia projekt: backend (FastAPI/uvicorn na porcie 8000) i frontend (Vite na porcie 5173).
# Wymaga wcześniejszego ./install.sh. Ctrl+C zatrzymuje oba procesy.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/services/backend"
FRONTEND_DIR="$ROOT_DIR/services/frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

info()  { echo "▶ $*"; }
fail()  { echo "❌ $*" >&2; exit 1; }

# --- 1. Sprawdzenie, czy instalacja została wykonana ------------------------
[ -x "$BACKEND_DIR/venv/bin/uvicorn" ] || fail "Brak backendu w venv. Najpierw uruchom ./install.sh"
[ -f "$BACKEND_DIR/.env" ]             || fail "Brak services/backend/.env. Uruchom ./install.sh"
[ -x "$FRONTEND_DIR/node_modules/.bin/vite" ] || fail "Brak zależności frontendu. Najpierw uruchom ./install.sh"

# Port już zajęty? Lepiej zatrzymać się z jasnym komunikatem niż dostać błąd z uvicorna/Vite.
port_in_use() {
    (echo > "/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
}
if port_in_use "$BACKEND_PORT"; then
    fail "Port $BACKEND_PORT jest zajęty. Zatrzymaj proces na tym porcie albo ustaw BACKEND_PORT=<port>."
fi
if port_in_use "$FRONTEND_PORT"; then
    fail "Port $FRONTEND_PORT jest zajęty. Zatrzymaj proces na tym porcie albo ustaw FRONTEND_PORT=<port>."
fi

# --- 2. Zatrzymywanie procesów po Ctrl+C / zakończeniu ----------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    info "Zatrzymywanie serwisów..."
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
    wait 2>/dev/null || true
    echo "👋 Do zobaczenia!"
}
trap cleanup EXIT INT TERM

# --- 3. Baza danych (idempotentne, bezpieczne przy każdym starcie) ----------
info "Backend: aktualizacja bazy danych..."
(
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source venv/bin/activate
    python -m sql_app.init_db
)

# --- 4. Backend --------------------------------------------------------------
info "Backend: http://127.0.0.1:$BACKEND_PORT (dokumentacja API: /docs)"
(
    cd "$BACKEND_DIR"
    exec venv/bin/uvicorn main:app --reload --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

# --- 5. Frontend -------------------------------------------------------------
info "Frontend: http://localhost:$FRONTEND_PORT"
(
    cd "$FRONTEND_DIR"
    exec ./node_modules/.bin/vite --port "$FRONTEND_PORT" --strictPort
) &
FRONTEND_PID=$!

echo ""
echo "🚀 Projekt działa. Otwórz http://localhost:$FRONTEND_PORT  (Ctrl+C = zatrzymanie)"
echo ""

# Czekamy, aż którykolwiek z procesów się zakończy (np. błąd startu lub Ctrl+C).
# Pętla zamiast `wait -n`, bo macOS domyślnie ma bash 3.2, który go nie obsługuje.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 1
done
echo "⚠️  Jeden z serwisów zakończył działanie."
