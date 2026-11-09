---
name: hotfix
description: Mały, odwracalny hotfix z testem i walidacją w location_service
argument-hint: <opis błędu i endpoint>
allowed-tools: Read, Grep, Edit, Write, Bash(pytest *), Bash(git diff *)
---
Zrób hotfix: $ARGUMENTS

Zasady: jeden endpoint, jeden plik źródłowy plus test, bez refaktoryzacji „przy okazji",
bez zmian w modelach i migracjach. Walidacja parametrów przez fastapi.Query.
Kryterium: `pytest -q` zielone. Na końcu pokaż `git diff --stat` i wypisz,
co sprawdzić ręcznie (curl).
