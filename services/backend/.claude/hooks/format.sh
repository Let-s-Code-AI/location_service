#!/usr/bin/env bash
# Hook PostToolUse (Edit|Write): formatuje edytowany plik Python.
# Używa ruff (venv/bin/ruff) jeśli jest zainstalowany; w przeciwnym razie no-op.
# Nigdy nie blokuje — błąd formatera nie może przerwać pracy agenta.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Tylko pliki Python, które istnieją na dysku.
case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

# Migracje nie są formatowane (zasada: bez zmian w migracjach).
case "$file" in
  */alembic/versions/*) exit 0 ;;
esac

if [ -x venv/bin/ruff ]; then
  venv/bin/ruff format --quiet "$file" >/dev/null 2>&1
fi

exit 0
