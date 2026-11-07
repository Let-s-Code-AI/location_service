#!/usr/bin/env bash
# Hook Stop: uruchamia `pytest -q` przed zakończeniem tury.
# Czerwone testy blokują zakończenie (Claude dostaje wynik i poprawia).
# Guard stop_hook_active: po jednej próbie poprawki nie blokujemy ponownie (brak pętli).

input=$(cat)
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -x venv/bin/pytest ] || exit 0

out=$(venv/bin/pytest -q 2>&1)
rc=$?

# 0 = ok, 5 = brak zebranych testów
if [ "$rc" -eq 0 ] || [ "$rc" -eq 5 ]; then
  exit 0
fi

tail_out=$(printf '%s\n' "$out" | tail -40)
active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')

if [ "$active" = "true" ]; then
  jq -n --arg m "pytest -q nadal czerwony po poprawce:"$'\n'"$tail_out" '{systemMessage: $m}'
  exit 0
fi

jq -n --arg r "pytest -q zakończył się błędem (kod $rc). Napraw testy, zanim skończysz:"$'\n'"$tail_out" \
  '{decision: "block", reason: $r}'
