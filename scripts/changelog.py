#!/usr/bin/env python3
"""Deterministic changelog for a pull request, built from Conventional Commits.

    python3 scripts/changelog.py                        # origin/main..HEAD -> Markdown on stdout
    python3 scripts/changelog.py --base <ref> --head <ref>
    python3 scripts/changelog.py --update-pr [--pr N]   # CI: write it into the PR body

The output is a pure function of the commit messages in the range: the same
set of messages renders byte-for-byte the same Markdown, whatever the commit
order, SHAs, authors or dates. That is what makes it safe to regenerate on
every push and to diff against a previous run:

- merge commits are skipped (`git log --no-merges`);
- subjects are parsed as `type(scope)!: subject`; a type outside SECTIONS or
  a subject that does not parse lands in the "Inne" section unchanged;
- sections come in the fixed order of SECTIONS, entries inside a section are
  sorted by scope (scoped entries first) and then by subject, using plain
  code-point order so the result does not depend on the machine's locale;
- identical entries are listed once;
- commits with `!` after the type/scope or a `BREAKING CHANGE:` footer are
  repeated in a leading "Zmiany łamiące kompatybilność" section.

`--update-pr` reads GITHUB_TOKEN, GITHUB_REPOSITORY and the PR number (from
`--pr` or the GITHUB_EVENT_PATH payload), then replaces the block between
MARKER_START and MARKER_END in the PR body, or appends the block when the
markers are missing. Nothing is sent when the body is already up to date.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MARKER_START = "<!-- changelog:start -->"
MARKER_END = "<!-- changelog:end -->"

# Section order and headings; "other" collects everything that is not a known type.
SECTIONS: tuple[tuple[str, str], ...] = (
    ("feat", "Nowe funkcje"),
    ("fix", "Poprawki"),
    ("perf", "Wydajność"),
    ("refactor", "Refaktoryzacja"),
    ("revert", "Cofnięte zmiany"),
    ("test", "Testy"),
    ("build", "Build"),
    ("ci", "CI"),
    ("docs", "Dokumentacja"),
    ("style", "Styl kodu"),
    ("chore", "Porządki"),
    ("other", "Inne"),
)
KNOWN_TYPES = frozenset(kind for kind, _ in SECTIONS) - {"other"}
BREAKING_HEADING = "Zmiany łamiące kompatybilność"

SUBJECT_RE = re.compile(
    r"^(?P<kind>[A-Za-z]+)(?:\((?P<scope>[^()]*)\))?(?P<bang>!)?:\s*(?P<subject>\S.*)$"
)
BREAKING_RE = re.compile(r"^BREAKING[ -]CHANGE:", re.MULTILINE)


@dataclass(frozen=True)
class Entry:
    kind: str
    scope: str
    subject: str
    breaking: bool = False


def parse_commit(message: str) -> Entry:
    """Turn a raw commit message (subject + body) into a changelog entry."""
    subject, _, body = message.strip().partition("\n")
    subject = subject.strip()
    match = SUBJECT_RE.match(subject)
    if match is None or match["kind"].lower() not in KNOWN_TYPES:
        return Entry("other", "", subject, bool(BREAKING_RE.search(body)))
    return Entry(
        kind=match["kind"].lower(),
        scope=(match["scope"] or "").strip(),
        subject=match["subject"].strip(),
        breaking=bool(match["bang"]) or bool(BREAKING_RE.search(body)),
    )


def sort_key(entry: Entry) -> tuple[bool, str, str, bool]:
    # Scoped entries first, grouped by scope, then by subject. Code-point
    # order on purpose: locale-aware collation would differ between machines.
    return (entry.scope == "", entry.scope, entry.subject, entry.breaking)


def render(entries: Iterable[Entry]) -> str:
    """Render entries as Markdown. Same entries in any order -> same string."""
    unique = sorted(set(entries), key=sort_key)
    lines = ["## Changelog", ""]
    if not unique:
        lines += ["_Brak commitów do wylistowania._", ""]
        return "\n".join(lines)
    breaking = [entry for entry in unique if entry.breaking]
    if breaking:
        lines += _section(BREAKING_HEADING, breaking)
    for kind, heading in SECTIONS:
        group = [entry for entry in unique if entry.kind == kind]
        if group:
            lines += _section(heading, group)
    return "\n".join(lines)


def _section(heading: str, entries: list[Entry]) -> list[str]:
    return [f"### {heading}", *(_bullet(entry) for entry in entries), ""]


def _bullet(entry: Entry) -> str:
    if entry.scope:
        return f"- **{entry.scope}**: {entry.subject}"
    return f"- {entry.subject}"


def git_messages(base: str, head: str, cwd: Path = REPO_ROOT) -> list[str]:
    """Raw messages of the non-merge commits in base..head (any order)."""
    result = subprocess.run(
        ["git", "log", "--no-merges", "--format=%B%x1e", f"{base}..{head}"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        message.strip() for message in result.stdout.split("\x1e") if message.strip()
    ]


def default_base(cwd: Path = REPO_ROOT) -> str:
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "origin/main"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    return "origin/main" if probe.returncode == 0 else "main"


def upsert_section(body: str, section: str) -> str:
    """Replace the marked block in a PR body, or append it when there is none."""
    block = f"{MARKER_START}\n{section.rstrip()}\n{MARKER_END}"
    start = body.find(MARKER_START)
    end = body.find(MARKER_END, start + len(MARKER_START)) if start != -1 else -1
    if start != -1 and end != -1:
        return body[:start] + block + body[end + len(MARKER_END) :]
    body = body.rstrip()
    return f"{body}\n\n{block}\n" if body else f"{block}\n"


def github_request(
    method: str, url: str, token: str, payload: dict | None = None
) -> dict:
    request = urllib.request.Request(
        url,
        method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def update_pr_body(repo: str, number: int, token: str, section: str) -> bool:
    """Write the section into the PR body. Returns False when nothing changed."""
    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
    # The web editor saves CRLF; normalise so an unchanged changelog compares equal.
    current = (github_request("GET", url, token)["body"] or "").replace("\r\n", "\n")
    updated = upsert_section(current, section)
    if updated == current:
        return False
    github_request("PATCH", url, token, {"body": updated})
    return True


def pr_number_from_event() -> int | None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    with open(event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    return event.get("pull_request", {}).get("number")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--base", help="base ref (default: origin/main, or main)")
    parser.add_argument("--head", default="HEAD", help="head ref (default: HEAD)")
    parser.add_argument(
        "--update-pr", action="store_true", help="write the changelog into the PR body"
    )
    parser.add_argument(
        "--pr", type=int, help="PR number (default: from GITHUB_EVENT_PATH)"
    )
    args = parser.parse_args(argv)

    base = args.base or default_base()
    section = render(parse_commit(message) for message in git_messages(base, args.head))
    sys.stdout.write(section)
    if not args.update_pr:
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    number = args.pr or pr_number_from_event()
    if not (token and repo and number):
        print(
            "--update-pr needs GITHUB_TOKEN, GITHUB_REPOSITORY and a PR number",
            file=sys.stderr,
        )
        return 2
    try:
        changed = update_pr_body(repo, number, token, section)
    except urllib.error.HTTPError as error:
        print(
            f"GitHub API {error.code}: {error.read().decode(errors='replace')}",
            file=sys.stderr,
        )
        return 1
    print(f"PR #{number}: {'opis zaktualizowany' if changed else 'opis bez zmian'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
