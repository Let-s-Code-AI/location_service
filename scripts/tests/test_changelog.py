"""Tests for scripts/changelog.py: parsing, deterministic rendering, PR body upsert."""

import os
import random
import subprocess

import changelog
import pytest
from changelog import (
    MARKER_END,
    MARKER_START,
    Entry,
    git_messages,
    parse_commit,
    render,
    update_pr_body,
    upsert_section,
)

# --- parse_commit -----------------------------------------------------------


def test_parse_subject_with_scope_and_body():
    message = "feat(backend): filtry ceny w GET /listings/\n\nOpis w treści."
    assert parse_commit(message) == Entry(
        "feat", "backend", "filtry ceny w GET /listings/"
    )


def test_parse_subject_without_scope_normalises_type_case():
    assert parse_commit("Fix:  przywróć import ") == Entry("fix", "", "przywróć import")


@pytest.mark.parametrize(
    "subject",
    [
        "Merge pull request #36 from org/feat",
        "wip: jeszcze nie",
        "zwykły opis bez typu",
    ],
)
def test_parse_unknown_subject_goes_to_other_unchanged(subject):
    assert parse_commit(subject) == Entry("other", "", subject)


@pytest.mark.parametrize(
    "message",
    [
        "feat(api)!: nowy kontrakt",
        "feat!: nowy kontrakt",
        "fix: x\n\nBREAKING CHANGE: inne pole",
        "fix: x\n\nBREAKING-CHANGE: inne pole",
    ],
)
def test_parse_marks_breaking_changes(message):
    assert parse_commit(message).breaking


def test_parse_breaking_only_from_footer_line_start():
    assert not parse_commit("fix: x\n\nto nie jest BREAKING CHANGE: w stopce").breaking


# --- render -----------------------------------------------------------------

MESSAGES = [
    "docs: README",
    "feat(frontend): panel filtrów",
    "Merge pull request #36 from org/feat",
    "fix(backend): migracja",
    "feat: bez scope",
    "feat(api)!: nowy kontrakt odpowiedzi",
    "feat(backend): filtry ceny",
    "feat(backend): filtry ceny",
]

GOLDEN = """## Changelog

### Zmiany łamiące kompatybilność
- **api**: nowy kontrakt odpowiedzi

### Nowe funkcje
- **api**: nowy kontrakt odpowiedzi
- **backend**: filtry ceny
- **frontend**: panel filtrów
- bez scope

### Poprawki
- **backend**: migracja

### Dokumentacja
- README

### Inne
- Merge pull request #36 from org/feat
"""


def test_render_golden():
    assert render(map(parse_commit, MESSAGES)) == GOLDEN


def test_render_does_not_depend_on_commit_order():
    shuffled = list(MESSAGES)
    for seed in range(10):
        random.Random(seed).shuffle(shuffled)
        assert render(map(parse_commit, shuffled)) == GOLDEN


def test_render_lists_identical_entries_once():
    out = render(
        map(parse_commit, ["ci: ponowne uruchomienie", "ci: ponowne uruchomienie"])
    )
    assert out == "## Changelog\n\n### CI\n- ponowne uruchomienie\n"


def test_render_keeps_fixed_section_order():
    out = render(
        map(parse_commit, ["docs: d", "test: t", "fix: x", "feat: f", "ci: c"])
    )
    headings = [line for line in out.splitlines() if line.startswith("### ")]
    assert headings == [
        "### Nowe funkcje",
        "### Poprawki",
        "### Testy",
        "### CI",
        "### Dokumentacja",
    ]


def test_render_uses_code_point_order_not_locale():
    out = render(map(parse_commit, ["feat: żaba", "feat: zebra", "feat: Zorro"]))
    assert out.splitlines()[3:] == ["- Zorro", "- zebra", "- żaba"]


def test_render_without_entries():
    assert render([]) == "## Changelog\n\n_Brak commitów do wylistowania._\n"


# --- upsert_section ---------------------------------------------------------


def test_upsert_into_empty_body():
    assert (
        upsert_section("", "## Changelog\n")
        == f"{MARKER_START}\n## Changelog\n{MARKER_END}\n"
    )


def test_upsert_appends_after_existing_description():
    out = upsert_section("Opis PR\n", "## Changelog\n")
    assert out == f"Opis PR\n\n{MARKER_START}\n## Changelog\n{MARKER_END}\n"


def test_upsert_replaces_marked_block_and_keeps_the_rest():
    body = f"Opis\n\n{MARKER_START}\nstare\n{MARKER_END}\n\nStopka\n"
    assert (
        upsert_section(body, "nowe\n")
        == f"Opis\n\n{MARKER_START}\nnowe\n{MARKER_END}\n\nStopka\n"
    )


def test_upsert_is_idempotent():
    once = upsert_section("Opis", "## Changelog\n")
    assert upsert_section(once, "## Changelog\n") == once


# --- git_messages -----------------------------------------------------------


def test_git_messages_skips_merges_and_commits_reachable_from_base(tmp_path):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }

    def git(*args):
        subprocess.run(
            ["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True
        )

    git("init", "-q", "-b", "main")
    git("commit", "-q", "--allow-empty", "-m", "chore: init")
    git("checkout", "-q", "-b", "feature")
    git(
        "commit", "-q", "--allow-empty", "-m", "feat(backend): filtry\n\nTreść commita."
    )
    git("checkout", "-q", "main")
    git("commit", "-q", "--allow-empty", "-m", "fix: tylko na mainie")
    git("checkout", "-q", "feature")
    git("merge", "-q", "--no-edit", "main")
    git("commit", "-q", "--allow-empty", "-m", "docs: po merge")

    messages = git_messages("main", "feature", cwd=tmp_path)
    assert sorted(messages) == [
        "docs: po merge",
        "feat(backend): filtry\n\nTreść commita.",
    ]


# --- update_pr_body / main --------------------------------------------------


def test_update_pr_body_patches_only_when_the_body_changes(monkeypatch):
    calls = []
    stored = {"body": "Opis\r\n"}  # the web editor saves CRLF

    def fake_request(method, url, token, payload=None):
        calls.append((method, url, token, payload))
        if method == "PATCH":
            stored["body"] = payload["body"]
        return {"body": stored["body"]}

    monkeypatch.setattr(changelog, "github_request", fake_request)

    assert update_pr_body("org/repo", 40, "tok", "## Changelog\n") is True
    method, url, token, payload = calls[-1]
    assert (method, url, token) == (
        "PATCH",
        "https://api.github.com/repos/org/repo/pulls/40",
        "tok",
    )
    assert payload == {"body": f"Opis\n\n{MARKER_START}\n## Changelog\n{MARKER_END}\n"}

    assert update_pr_body("org/repo", 40, "tok", "## Changelog\n") is False
    assert [call[0] for call in calls] == ["GET", "PATCH", "GET"]


def test_main_prints_changelog(monkeypatch, capsys):
    monkeypatch.setattr(changelog, "git_messages", lambda base, head: ["feat(x): a"])
    assert changelog.main(["--base", "b", "--head", "h"]) == 0
    assert capsys.readouterr().out == "## Changelog\n\n### Nowe funkcje\n- **x**: a\n"


def test_main_update_pr_requires_token_repo_and_number(monkeypatch, capsys):
    monkeypatch.setattr(changelog, "git_messages", lambda base, head: [])
    for name in ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_EVENT_PATH"):
        monkeypatch.delenv(name, raising=False)
    assert changelog.main(["--base", "b", "--update-pr"]) == 2
    assert "GITHUB_TOKEN" in capsys.readouterr().err
