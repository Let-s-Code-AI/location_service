# CLAUDE.md

Repo-wide rules for Claude Code. Service-specific guidance lives in `services/<service>/CLAUDE.md`.

## Code comments

- Write all code comments in **English**: inline comments, docstrings, and file headers, in every service (backend, frontend, e2e).
- Many existing comments are still in Polish. Translate a comment to English only when you change the code it describes; don't rewrite comments in unrelated code.
- This rule covers comments only. User-facing UI text, API error messages (`detail`), test names, and requirement docs (`user_stories*.md`, `.agent/plans/`) stay in their current language.
