#!/usr/bin/env bash
# Hook PostToolUse (Edit|Write|MultiEdit): po zapisie sql_app/models.py regeneruje
# docs/models.md (katalog główny repo) skryptem scripts/gen_model_docs.py.
# Dla innych plików kończy się natychmiast. Wynik trafia do kontekstu Claude
# (additionalContext), żeby wiedział, że docs/models.md też się zmienił.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$file" in
  */sql_app/models.py|sql_app/models.py) ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -x venv/bin/python ] || exit 0

out=$(venv/bin/python scripts/gen_model_docs.py 2>&1)
rc=$?

if [ "$rc" -ne 0 ]; then
  tail_out=$(printf '%s\n' "$out" | tail -15)
  jq -n --arg m "Generator dokumentacji modeli (scripts/gen_model_docs.py) zakończył się błędem (kod $rc), docs/models.md NIE został odświeżony:"$'\n'"$tail_out" \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $m}}'
  exit 0
fi

jq -n --arg m "Hook gen-model-docs: $out" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $m}}'
