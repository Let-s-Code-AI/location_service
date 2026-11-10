#!/usr/bin/env bash
# Starts the project: backend (FastAPI/uvicorn on port 8000) and frontend (Vite on port 5173).
# Requires running ./install.sh first. Ctrl+C stops both processes.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/services/backend"
FRONTEND_DIR="$ROOT_DIR/services/frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

info()  { echo "▶ $*"; }
fail()  { echo "❌ $*" >&2; exit 1; }

# --- 1. Check if installation was performed ------------------------
[ -x "$BACKEND_DIR/venv/bin/uvicorn" ] || fail "Backend not found in venv. Run ./install.sh first."
[ -f "$BACKEND_DIR/.env" ]             || fail "services/backend/.env not found. Run ./install.sh"
[ -x "$FRONTEND_DIR/node_modules/.bin/vite" ] || fail "Frontend dependencies missing. Run ./install.sh first."

# Port already in use? Better to stop with a clear message than get an error from uvicorn/Vite.
port_in_use() {
    (echo > "/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
}
if port_in_use "$BACKEND_PORT"; then
    fail "Port $BACKEND_PORT is in use. Stop the process on this port or set BACKEND_PORT=<port>."
fi
if port_in_use "$FRONTEND_PORT"; then
    fail "Port $FRONTEND_PORT is in use. Stop the process on this port or set FRONTEND_PORT=<port>."
fi

# --- 2. Stopping processes after Ctrl+C / termination ----------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    info "Stopping services..."
    # First children (e.g., uvicorn --reload worker), then the processes themselves.
    for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
        [ -n "$pid" ] && pkill -P "$pid" 2>/dev/null || true
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "👋 See you!"
}
trap cleanup EXIT INT TERM

# --- 3. Database (idempotent, safe on every start) -----------------------
info "Backend: updating database..."
(
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source venv/bin/activate
    python -m sql_app.init_db
)

# --- 4. Backend --------------------------------------------------------------
info "Backend: http://127.0.0.1:$BACKEND_PORT (API documentation: /docs)"
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
echo "🚀 Project is running. Open http://localhost:$FRONTEND_PORT  (Ctrl+C = stop)"
echo ""

# Wait until either process ends (e.g., startup error or Ctrl+C).
# Loop instead of `wait -n`, because macOS defaults to bash 3.2, which does not support it.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 1
done
echo "⚠️  One of the services has terminated."
