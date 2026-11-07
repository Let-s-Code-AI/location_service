# Plan: lista ogłoszeń (GET /listings/ + widok w UI)

Baza: branch `feat/location-description`, HEAD `717b1fd`. Bramki na starcie zielone:
`pytest -q` = 23 passed, `npm run build` = OK.

**Zakres:** `services/backend/{main.py, sql_app/schemas.py, tests/api/}`, `services/frontend/src/`, `*.md`
**Poza zakresem:** `alembic/`, `sql_app/models.py`, `.github/`, `.agent/` (poza tym plikiem), `package*.json`, `App.css`

## Tabela commitów

| # | Commit (conventional) | Serwis | Pliki | Weryfikacja | Budżet |
|---|-----------------------|--------|-------|-------------|--------|
| 1 | `feat(backend): schematy LocationSummary i ListingSummary` | backend | `sql_app/schemas.py` | `pytest -q` (import + regresja) | 20 l. / 1 plik |
| 2 | `feat(backend): GET /listings/ z paginacją i limitem 500` | backend | `main.py`, `tests/api/test_listings.py` (nowy) | `pytest -q` | 120 l. / 2 pliki |
| 3 | `feat(frontend): listListings w kliencie API` | frontend | `src/api.js` | `npm run build` | 10 l. / 1 plik |
| 4 | `feat(frontend): widok ListingsTable przełączany w App` | frontend | `src/ListingsTable.jsx` (nowy), `src/App.jsx` | `npm run build` + ręcznie `npm run dev` | 130 l. / 2 pliki |
| 5 | `docs: GET /listings/ w README i CLAUDE.md` | oba | `README.md`, `services/backend/README.md`, `services/backend/CLAUDE.md`, `services/frontend/README.md` | `grep -rn "no endpoints yet" services/backend/CLAUDE.md` zwraca pusto; przegląd | 40 l. / 4 pliki |

Kolejność: kontrakt → backend → frontend → docs. Każdy krok kończy się zieloną bramką swojego serwisu,
potem `git diff --stat` i tag `cp/<n>`.

## Co dokładnie wchodzi w każdy krok

### 1. Kontrakt (STOP po tym kroku, do akceptacji)

```python
class LocationSummary(BaseModel):
    city: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ListingSummary(BaseModel):
    listing_id: int
    rooms: Optional[int] = None
    area: Optional[float] = None
    price_total_zl: Optional[float] = None
    location: LocationSummary
    model_config = ConfigDict(from_attributes=True)
```

Dlaczego zagnieżdżone `location.city`, a nie płaskie `city`: `from_attributes=True` mapuje relację
bez `computed_field`, ten sam wzorzec co istniejący `ListingDetail`. Frontend spłaszcza po swojej
stronie (jak `toRow` w `App.jsx`).

### 2. Endpoint + testy w jednym commicie

- `GET /listings/` publiczny, jak `GET /locations/` (bez `get_current_user`).
- `skip: int = Query(0, ge=0)`, `limit: int = Query(100, ge=1, le=500)`.
- `select(models.Listing).options(selectinload(models.Listing.location)).order_by(models.Listing.listing_id)`.
  `selectinload` jest konieczny: w sesji async leniwe `listing.location` przy serializacji rzuca
  `MissingGreenlet`. Przy okazji zamyka N+1. `order_by` daje deterministyczną paginację.
- `response_model=List[schemas.ListingSummary]`.
- Testy (`tests/api/test_listings.py`), setup przez fixture `db` jak w
  `test_delete_location_used_by_listing_returns_409` (Listing ma 4 non-null FK):
  - pusta baza → `[]`
  - jeden rekord → `listing_id, rooms, area, price_total_zl, location.city`; **brak** `url`,
    `description_text` w odpowiedzi (to test kontraktu „summary”)
  - `skip=1&limit=1` zwraca drugi rekord
  - `limit=501` → 422, `skip=-1` → 422

### 3. Klient API

```js
// Listings
export const listListings = () => request('/listings/')
```

### 4. Widok

- `src/ListingsTable.jsx`: `useEffect` + `listListings`, stany `loading / error / empty`,
  tabela: Pokoje, Metraż, Cena, Miasto. **Tylko istniejące klasy CSS** (`card`, `table-wrap`,
  `alert`, `empty-state`, `id-badge`), zero zmian w `App.css`.
- `App.jsx`: stan `view` (`'locations' | 'listings'`) i dwa przyciski w nagłówku; ok. 15 linii.
  Komponent `Locations` zostaje w miejscu (patrz „rozważone i odrzucone”).

### 5. Dokumentacja

- `README.md` (root): status backendu i frontendu w tabeli serwisów.
- `services/backend/README.md`: sekcja API, `GET /listings/`.
- `services/backend/CLAUDE.md`: zdanie „`Listing` have models and schemas but no endpoints yet”
  jest po kroku 2 nieprawdziwe. To jest kontekst dla kolejnych sesji agenta, więc musi być aktualne.
- `services/frontend/README.md`: widok ogłoszeń.

## Decyzje do zatwierdzenia przed kodem

| # | Decyzja | Wybór w planie | Alternatywa |
|---|---------|----------------|-------------|
| D1 | Kształt `location.city` | zagnieżdżony `location: {city}` | płaskie `city` przez `computed_field` |
| D2 | Autoryzacja `GET /listings/` | publiczny, jak `GET /locations/` | wymagany token |
| D3 | Limit 500 | tylko nowy endpoint | ujednolicić też `/locations/` → **osobny wpis**, nie „przy okazji” |
| D4 | Sortowanie | `ORDER BY listing_id` | brak (jak `/locations/` dziś) |

## Rozważone i odrzucone (świadomie poza tym planem)

- **`refactor(frontend): wydziel Locations.jsx z App.jsx`**: czysty move ok. 350 linii, 2× ponad budżet;
  przełącznik widoku da się dodać w 15 liniach bez tego. Kandydat na osobny PR.
- **Test dymny frontendu (vitest)**: dotyka `package.json` i `package-lock.json`, poza zakresem.
  Osobny wpis; luka pozostaje zauważona.
- **Seed danych `listing`**: ręczna weryfikacja UI wymaga wierszy w tabeli `listing`, a nie ma
  `POST /listings/`. Osobny wpis (`scripts/seed_listings.py`) albo SQL na kopii bazy.
- **Cap `limit` w `/locations/`**: zmiana zachowania istniejącego endpointu, patrz D3.

## Strażnik zakresu

```bash
ALLOWED='^services/(backend/(main\.py|sql_app/schemas\.py|tests/api/)|frontend/src/)|\.md$'
OUT=$(git diff --name-only 717b1fd...HEAD | grep -vE "$ALLOWED")
[ -z "$OUT" ] || { echo "Pliki poza zakresem:"; echo "$OUT"; exit 1; }
```

## Protokół wykonania

```text
Wykonaj commit #N z .agent/plans/listings.md. Tylko ten commit.
1. komenda weryfikacji z tabeli,
2. git diff --stat, strażnik zakresu,
3. zielone i w budżecie → commit z komunikatem z planu, git tag cp/N,
4. stop, czekaj na "dalej".
Odchylenie (nowy plik, >1.5× budżetu) → zgłoś, nie wykonuj.
```
