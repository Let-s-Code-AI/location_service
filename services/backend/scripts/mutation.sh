#!/usr/bin/env bash
# Mutation testing for the backend: mutmut run + a minimum mutation score.
# Run from any directory; it changes into services/backend itself.
#
#   ./scripts/mutation.sh                        # fails below MUTATION_SCORE_MIN (default 75)
#   MUTATION_SCORE_MIN=0 ./scripts/mutation.sh   # report only
#
# mutmut is configured in pyproject.toml ([tool.mutmut]). It copies the sources
# and tests into mutants/ (git-ignored) and caches results there, so a second
# run only retests mutants whose code or tests changed; delete mutants/ for a
# full run. Afterwards: `mutmut results` lists the survivors, `mutmut show
# <name>` prints one mutant as a diff and `mutmut browse` opens the TUI.
# The score is computed the way mutmut does it: (killed + timeout) / tested.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ -x venv/bin/mutmut ]; then
    PATH="$PWD/venv/bin:$PATH"
fi

MIN="${MUTATION_SCORE_MIN:-75}"

echo "▶ Testy mutacyjne: mutmut run"
mutmut run

mutmut export-cicd-stats >/dev/null

summary=$(python - <<'PY'
import json

stats = json.load(open("mutants/mutmut-cicd-stats.json"))
tested = stats["total"] - stats["skipped"]
killed = stats["killed"] + stats["timeout"]
score = 100 * killed / tested if tested else 0.0
print(f"{score:.1f} {killed} {tested} {stats['survived']}")
PY
)
read -r score killed tested survived <<< "$summary"

echo "Mutanty: zabite ${killed}/${tested}, przeżyły ${survived} (lista: mutmut results)"
echo "Wynik mutacji: ${score}% (próg: ${MIN}%)"

if python -c "import sys; sys.exit(0 if float('$score') >= float('$MIN') else 1)"; then
    echo "✅ Testy mutacyjne backendu: OK"
else
    echo "❌ Wynik mutacji poniżej progu ${MIN}%"
    exit 1
fi
