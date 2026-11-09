# Plan: filtrowanie ofert (zakresy cen i metrażu, pokoje, autouzupełnianie lokalizacji, licznik, reset)

Brief: treść zadania (wymagania podane wprost, bez pliku briefu). Baza: branch `main`, HEAD `af01bb8`, drzewo czyste. Bramki na starcie:
`pytest -q` = 23 passed, `npm run build` = OK.

**Stan wyjściowy, który kształtuje plan:**
- `GET /listings/` **nie istnieje**: plan `.agent/plans/listings.md` nie został wykonany (`main.py` ma tylko `/auth/*` i `/locations/*`).
  Ten plan go zastępuje, patrz D1.
- Pola z briefu istnieją, nazwy się zgadzają: `Listing.price_total_zl` (Float), `Listing.price_sqm_zl` (Float), `Listing.area` (Float),
  `Listing.rooms` (Integer), wszystkie nullable. `city` i `city_district` **nie są w `Listing`**, tylko w `Location` (String(255), nullable),
  dostępne przez relację `Listing.location` (FK `location_id` non-null). Brak indeksów poza PK.
- Frontend nie ma runnera testów (`package.json`: tylko `vite`, `react`). Brief wymaga testów frontendu, więc wchodzi commit `build(frontend)`.
- Lokalna `sql_app.db` ma 0 wierszy w `listing` i nie ma `POST /listings/`: ręczna kontrola UI jest możliwa tylko częściowo (patrz krok 10).
- `docs/schema.md` (katalog główny repo, nie backend) jest generowany z `models.py` hookiem PostToolUse. Plan nie zmienia `models.py`,
  więc dokument się nie zregeneruje i nie jest edytowany.

**Zakres:**
`services/backend/main.py`, `services/backend/sql_app/schemas.py`, `services/backend/tests/conftest.py`,
`services/backend/tests/api/` (nowe: `test_listings.py`, `test_listing_filters.py`, `test_listing_suggestions.py`),
`services/frontend/package.json`, `services/frontend/package-lock.json`, `services/frontend/vite.config.js`,
`services/frontend/src/api.js`, `services/frontend/src/App.jsx`, `services/frontend/src/App.css`,
`services/frontend/src/` (nowe: `listingFilters.js`, `listingFilters.test.js`, `Autocomplete.jsx`, `Autocomplete.test.jsx`,
`ListingFilters.jsx`, `ListingFilters.test.jsx`, `ListingsView.jsx`, `ListingsView.test.jsx`),
`README.md`, `services/backend/README.md`, `services/backend/CLAUDE.md`, `services/frontend/README.md`.

**Poza zakresem:** `services/backend/sql_app/models.py`, `services/backend/alembic/`, `services/backend/sql_app/schema.sql`,
`docs/schema.md` (generowany), `services/e2e/`, `.github/`, `.agent/` (poza tym plikiem, w tym `.agent/plans/listings.md`),
istniejące endpointy `/locations/*` i `/auth/*`, `services/frontend/src/{Login.jsx,ui.jsx,main.jsx}`.

## Tabela commitów

| # | Commit (conventional) | Serwis | Pliki | Weryfikacja | Budżet |
|---|-----------------------|--------|-------|-------------|--------|
| 1 | `feat(backend): schematy ListingSummary i ListingPage dla listy ofert` | backend | `sql_app/schemas.py` | `pytest -q` (wyjątek: zmiana czysto schematowa, import + regresja) | 30 l. / 1 plik |
| 2 | `feat(backend): GET /listings/ z paginacją i polem total` | backend | `main.py`, `tests/conftest.py`, `tests/api/test_listings.py` (nowy) | `pytest -q` | 130 l. / 3 pliki |
| 3 | `feat(backend): filtry ceny, ceny za m², metrażu i pokoi w GET /listings/` | backend | `main.py`, `tests/api/test_listing_filters.py` (nowy) | `pytest -q` | 180 l. / 2 pliki |
| 4 | `feat(backend): filtry city i city_district w GET /listings/` | backend | `main.py`, `tests/api/test_listing_filters.py` | `pytest -q` | 70 l. / 2 pliki |
| 5 | `feat(backend): GET /listings/suggestions z podpowiedziami miast i dzielnic` | backend | `main.py`, `tests/api/test_listing_suggestions.py` (nowy) | `pytest -q` | 140 l. / 2 pliki |
| 6 | `build(frontend): vitest, Testing Library i jsdom jako runner testów` | frontend | `package.json`, `package-lock.json`, `vite.config.js` | `npm install && npm test && npm run build` | 20 l. ręcznie + lock (generowany) / 3 pliki |
| 7 | `feat(frontend): stan filtrów, query string i klient listListings/suggestListingValues` | frontend | `src/listingFilters.js` (nowy), `src/listingFilters.test.js` (nowy), `src/api.js` | `npm test && npm run build` | 140 l. / 3 pliki |
| 8 | `feat(frontend): komponent Autocomplete z debounce i obsługą klawiatury` | frontend | `src/Autocomplete.jsx` (nowy), `src/Autocomplete.test.jsx` (nowy), `src/App.css` | `npm test && npm run build` | 180 l. / 3 pliki |
| 9 | `feat(frontend): panel ListingFilters z licznikiem wyników i resetem` | frontend | `src/ListingFilters.jsx` (nowy), `src/ListingFilters.test.jsx` (nowy), `src/App.css` | `npm test && npm run build` | 190 l. / 3 pliki |
| 10 | `feat(frontend): widok ofert z filtrami przełączany w App` | frontend | `src/ListingsView.jsx` (nowy), `src/ListingsView.test.jsx` (nowy), `src/App.jsx` | `npm test && npm run build` + ręcznie `npm run dev` (częściowo, patrz krok 10) | 200 l. / 3 pliki |
| 11 | `docs: filtrowanie ofert i testy frontendu w README i CLAUDE.md` | docs | `README.md`, `services/backend/README.md`, `services/backend/CLAUDE.md`, `services/frontend/README.md` | z katalogu głównego: `grep -n "no endpoints yet" services/backend/CLAUDE.md` i `grep -n "Only the \`Location\` resource" services/backend/README.md` zwracają pusto; `grep -n "npm test" services/frontend/README.md` i `grep -n "/listings/suggestions" services/backend/README.md` zwracają trafienie | 60 l. / 4 pliki |

Kolejność: kontrakt → backend → frontend → docs (e2e poza briefem). Każdy krok kończy się zieloną bramką swojego serwisu,
potem `git diff --stat` i tag `cp/<n>`.

## Co dokładnie wchodzi w każdy krok

### 1. Kontrakt (STOP po tym kroku, do akceptacji)

```python
class LocationSummary(BaseModel):
    city: Optional[str] = None
    city_district: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ListingSummary(BaseModel):
    listing_id: int
    rooms: Optional[int] = None
    area: Optional[float] = None
    price_total_zl: Optional[float] = None
    price_sqm_zl: Optional[float] = None
    location: LocationSummary
    model_config = ConfigDict(from_attributes=True)

class ListingPage(BaseModel):
    items: List[ListingSummary]
    total: int          # liczba ofert po filtrach, niezależna od skip/limit
    skip: int
    limit: int
```

Do akceptacji razem ze schematami (sygnatury, kod w krokach 2–5):
- `GET /listings/?skip=0&limit=50&price_total_min&price_total_max&price_sqm_min&price_sqm_max&area_min&area_max&rooms=2&rooms=3&city&city_district` → `ListingPage`.
- `GET /listings/suggestions?field=city|city_district&q=Kra&city=<opcjonalnie>&limit=10` → `List[str]`.

Uzasadnienie: zagnieżdżone `location` przez `from_attributes=True` to wzorzec `ListingDetail` (i D1 z `listings.md`).
Licznik jako `total` w kopercie odpowiedzi, a nie osobny `/listings/count`: jedno żądanie na zmianę filtrów, licznik i lista
zawsze z tego samego zestawu filtrów (brak rozjazdu przy wyścigu dwóch żądań), a endpoint jest nowy, więc koperta nie łamie
żadnego klienta. Koszt: drugie zapytanie `COUNT` na serwerze, przy SQLite i tej skali pomijalny (D2).

### 2. Lista ofert bez filtrów + `total`

- `GET /listings/` publiczny jak `GET /locations/`; `skip: int = Query(0, ge=0)`, `limit: int = Query(50, ge=1, le=500)`,
  `response_model=schemas.ListingPage`.
- Zapytanie: `select(models.Listing).options(selectinload(models.Listing.location)).order_by(models.Listing.listing_id)`.
  `selectinload` obowiązkowy (leniwe `listing.location` w sesji async rzuca `MissingGreenlet`), `order_by` daje stabilną paginację.
- `total`: `select(func.count()).select_from(models.Listing)` z **tą samą listą warunków** co zapytanie o wiersze. Już w tym kroku
  warunki budować jako listę `conditions` stosowaną do obu zapytań, żeby kroki 3–4 tylko ją rozszerzały (bez duplikacji `where`).
- `tests/conftest.py`: fixture `make_listing` (fabryka async), która tworzy `Location`/`Building`/`Owner`/`Features` i `Listing`
  z podanymi polami; wzorzec setupu z `test_delete_location_used_by_listing_returns_409` (4 non-null FK). Używana w krokach 2–5.
- Testy (`test_listings.py`): pusta baza → `items=[]`, `total=0`; jeden rekord → pola summary + `location.city`/`city_district`,
  **brak** `url` i `description_text` (kontrakt summary); 3 rekordy, `skip=1&limit=1` → drugi rekord i `total=3`;
  `limit=0`, `limit=501`, `skip=-1` → 422.

### 3. Filtry liczbowe

- Zależność `listing_filters(...)` w `main.py` (FastAPI 0.104 nie obsługuje modeli Pydantic jako query, więc zwykła funkcja-zależność):
  `price_total_min/max`, `price_sqm_min/max`, `area_min/max`: `Optional[float] = Query(None, ge=0)`;
  `rooms: List[int] = Query([])` (powtarzany parametr `rooms=2&rooms=3`).
- Walidacja w zależności, `HTTPException(422, detail="<pole>_min nie może być większe niż <pole>_max")`: min > max, wartość
  nieskończona (`inf` przechodzi przez `ge=0`, sprawdzić `math.isfinite`), `rooms` < 1. Detail jako string, bo `src/api.js`
  pokazuje `body.detail` tylko gdy jest stringiem (D4).
- Warunki: `>=`/`<=` (granice włącznie), `rooms` → `Listing.rooms.in_(rooms)`. Oferty z `NULL` w filtrowanym polu wypadają
  z wyniku tylko wtedy, gdy dany filtr jest ustawiony (semantyka SQL, D5).
- Testy (`test_listing_filters.py`): każdy zakres osobno (min, max, oba; granica włącznie); `NULL` wykluczony przy aktywnym filtrze
  i obecny bez filtra; `rooms` jedna i dwie wartości; kombinacja filtrów; `total` odzwierciedla filtry, nie stronę (`limit=1`);
  422: min > max dla każdej pary, wartość ujemna, `rooms=0`, `price_total_min=inf`.

### 4. Filtry lokalizacji

- `city: Optional[str] = Query(None, max_length=255)`, `city_district` analogicznie. Gdy któryś ustawiony: `join(models.Listing.location)`
  w obu zapytaniach (wiersze i `total`), porównanie dokładne `Location.city == city` (wartości pochodzą z podpowiedzi, D6).
- Pułapka: `join` + `selectinload` na tej samej relacji jest poprawny (selectinload robi osobne zapytanie), ale `join` musi trafić
  też do zapytania `COUNT`, inaczej `total` liczy bez filtra.
- Testy (dopisane do `test_listing_filters.py`): `city` zawęża; `city` + `city_district` zawęża; nieistniejące miasto → `total=0`;
  kombinacja z filtrem ceny.

### 5. Endpoint podpowiedzi

- `GET /listings/suggestions`, zadeklarowany **przed** ewentualnym przyszłym `/listings/{listing_id}` (inaczej `suggestions` trafi
  do path-param). `field: Literal["city", "city_district"]`, `q: str = Query("", max_length=100)`,
  `city: Optional[str] = Query(None)` (zawęża dzielnice), `limit: int = Query(10, ge=1, le=50)`, `response_model=List[str]`.
- Zapytanie: `select(distinct(kolumna)).join(Listing)` (tylko lokalizacje, które mają oferty, D7), `kolumna IS NOT NULL`,
  `kolumna.like(f"{q_escaped}%", escape="\\")` z escapowaniem `%`, `_`, `\`; `order_by(kolumna)`; `limit`.
- Testy (`test_listing_suggestions.py`): pusto → `[]`; prefiks `Kra` → `["Kraków"]`; distinct (dwie oferty w tym samym mieście → jedna
  wartość); sortowanie; `NULL` pominięty; lokalizacja bez ofert pominięta; `field=city_district&city=Kraków` zwraca tylko dzielnice
  Krakowa; `limit=1`; `q=%` nie zwraca wszystkiego; `field=street` → 422; `limit=51` → 422.

### 6. Runner testów frontendu

- `devDependencies`: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom` (wersje zgodne z Vite 7 / React 19,
  instalowane `npm install -D`, lock generowany). Skrypt `"test": "vitest run --passWithNoTests"` (pierwszy test wchodzi w kroku 7).
- `vite.config.js`: blok `test: { environment: 'jsdom', globals: true }` (`globals` włącza auto-cleanup Testing Library).
- Bez `@testing-library/jest-dom`: asercje przez zwykłe `expect` na elementach, mniej zależności (D8).

### 7. Model filtrów i klient API

- `src/listingFilters.js`: `EMPTY_FILTERS`, `isEmptyFilters(f)`, `validateFilters(f)` (min > max, ujemne → mapa błędów po polu),
  `toQuery(f, {skip, limit})` (pomija puste, `rooms` jako powtarzany parametr przez `URLSearchParams.append`),
  `pluralOffers(n)` (1 oferta / 2–4 oferty / 5+ ofert, z wyjątkiem 12–14).
- `src/api.js`: `listListings(filters, page)` → `request('/listings/?' + toQuery(...))`,
  `suggestListingValues(field, q, city)` → `request('/listings/suggestions?...')`. Wzorzec istniejących eksportów (`listLocations`).
- Testy (`listingFilters.test.js`): `toQuery` pomija puste i powtarza `rooms`; `validateFilters` dla min > max i wartości ujemnej;
  `isEmptyFilters`; `pluralOffers(0/1/2/5/12/22)`.

### 8. Autocomplete

- Kontrolowany komponent: props `id`, `label`, `value`, `onChange`, `fetchSuggestions(q)` (wstrzykiwane, więc test nie mockuje
  `fetch`), `placeholder`. Opakowanie w istniejące klasy `field` / `input-wrap` (jak `Field` z `ui.jsx`, ale bez jego modyfikacji).
- Debounce 250 ms, ignorowanie spóźnionych odpowiedzi (licznik żądań w `useRef`), `role="combobox"` + `role="listbox"`/`option`,
  strzałki, Enter wybiera, Escape zamyka, błąd fetchu → brak listy bez alertu.
- `App.css`: ok. 30 linii dla `.suggestions` (lista rozwijana pod polem), w zmiennych kolorów już używanych w pliku.
- Testy: wpisanie tekstu → `fetchSuggestions` wołany raz po debounce z ostatnią wartością (`vi.useFakeTimers` + `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })`);
  kliknięcie podpowiedzi → `onChange(wartość)` i zamknięcie listy; strzałka + Enter; Escape; spóźniona odpowiedź nie nadpisuje nowszej.

### 9. Panel filtrów

- Komponent prezentacyjny: props `filters`, `errors`, `total`, `loading`, `onChange(patch)`, `onReset`, `fetchSuggestions`.
  Pola `type="number" min="0"` dla trzech zakresów, checkboxy pokoi 1–5 (D9), dwa `Autocomplete` (dzielnica dostaje `city`
  do zawężenia podpowiedzi). Licznik „Znaleziono N ofert” z `pluralOffers`, `aria-live="polite"`. Przycisk „Wyczyść filtry”
  `disabled` gdy `isEmptyFilters`.
- `App.css`: ok. 20 linii dla siatki zakresów i chipów pokoi; reszta to istniejące `card`, `form-grid`, `btn`, `btn-ghost`, `hint`.
- Testy: zmiana `price_total_min` → `onChange({price_total_min: '...'})`; zaznaczenie/odznaczenie pokoju; błąd z `errors` widoczny
  przy polu; licznik pokazuje `total` z poprawną odmianą; reset woła `onReset` i jest wyłączony przy pustych filtrach.

### 10. Widok ofert

- `src/ListingsView.jsx`: stan `filters`, walidacja `validateFilters`, przy poprawnych filtrach debounce 300 ms i `listListings`,
  przy zmianie filtrów `skip` wraca do 0; ignorowanie spóźnionych odpowiedzi; stany `loading / error / empty` jak w `Locations`
  (`alert`, `empty-state`, `loading-cell`); tabela: Miasto, Dzielnica, Pokoje, Metraż, Cena, Cena/m²; stopka `table-foot`
  „Wyświetlono X z total”. Reset ustawia `EMPTY_FILTERS` i odświeża natychmiast (bez debounce).
- `App.jsx`: stan `view` (`'locations' | 'listings'`) i dwa przyciski `btn btn-ghost` nad widokiem, ok. 15 linii; `Locations` bez zmian.
- Testy (`vi.mock('./api.js')`): pierwsze renderowanie woła `listListings` z pustymi filtrami i pokazuje licznik; zmiana filtra →
  nowe wywołanie po debounce i nowy licznik; min > max → brak wywołania i komunikat; reset → wywołanie z pustymi filtrami.
- Ręcznie (`npm run dev` + backend): lokalna baza ma 0 ofert, więc da się sprawdzić tylko przełączanie widoku, pusty stan,
  licznik „0 ofert”, walidację min > max, reset i brak błędów w konsoli/Network (żądania `/api/listings/` z poprawnym query).
  Lista z wynikami i podpowiedzi wymagają danych (patrz „Rozważone i odrzucone”: seed).

### 11. Dokumentacja

- `services/backend/CLAUDE.md`: zdanie „`Listing` have models and schemas but no endpoints yet” staje się nieprawdziwe po kroku 2;
  opisać `GET /listings/` (filtry, `total`) i `/listings/suggestions`.
- `services/backend/README.md`: linia statusu („Only the `Location` resource…”) i tabela API: dwa nowe wiersze + przykład `curl` z filtrami.
- `services/frontend/README.md`: zdanie „It currently manages `Location` records…”, sekcja struktury (nowe pliki), `npm test`.
- `README.md` (root): kolumna statusu backendu i frontendu.
- `docs/schema.md` bez zmian (generowany, `models.py` nietknięty).

## Decyzje do zatwierdzenia przed kodem

| # | Decyzja | Wybór w planie | Alternatywa |
|---|---------|----------------|-------------|
| D1 | Relacja do niewykonanego `listings.md` | ten plan go zastępuje (koperta `ListingPage` zamiast `List[ListingSummary]`); `listings.md` nie wykonywać; przejęte D1/D2/D4 stamtąd (zagnieżdżone `location`, publiczny GET, `ORDER BY listing_id`) | wykonać najpierw `listings.md`, filtry dobudować i licznik dać jako osobny `/listings/count` (lista zostaje gołą tablicą) |
| D2 | Licznik wyników | `total` w odpowiedzi listy (jedno żądanie, spójny z listą) | osobny `GET /listings/count` z tymi samymi filtrami (dwa żądania, ryzyko rozjazdu) |
| D3 | Paginacja | `limit` domyślnie 50, `le=500`; UI pokazuje pierwszą stronę i „X z total” | pełne przyciski Poprzednia/Następna w UI (osobny wpis) |
| D4 | Format błędu walidacji krzyżowej | `HTTPException(422)` ze stringiem w `detail` (czytelny w `api.js`) | `RequestValidationError` z listą błędów jak w FastAPI (UI pokaże tylko „HTTP 422”) |
| D5 | Oferty z `NULL` w filtrowanym polu | wykluczone, gdy filtr na to pole jest aktywny | zawsze uwzględniane (`OR pole IS NULL`) |
| D6 | Dopasowanie `city`/`city_district` w filtrze | dokładne `==` (wartość z podpowiedzi) | `LIKE` / case-insensitive (SQLite `lower()` nie składa polskich znaków) |
| D7 | Źródło podpowiedzi | tylko lokalizacje, które mają oferty (`JOIN listing`), więc wybór nie da 0 wyników | wszystkie wiersze `location` (bez joina) |
| D8 | Stos testów frontendu | `vitest` + `@testing-library/react` + `user-event` + `jsdom`, bez `jest-dom` | `jest` + `babel` (więcej konfiguracji przy Vite) |
| D9 | Opcje pokoi | checkboxy 1–5, dopasowanie dokładne | „5+” jako `rooms_min` (osobny parametr) |
| D10 | Autoryzacja nowych GET | publiczne, jak `GET /locations/` | wymagany token |

## Rozważone i odrzucone (świadomie poza tym planem)

- **`perf(backend): indeksy na listing.price_total_zl, price_sqm_zl, area, rooms`**: wymaga `models.py` + migracji Alembic
  (i regeneracji `docs/schema.md` przez hook); przy SQLite i obecnej skali bez mierzalnego zysku. Osobny wpis, gdy dane urosną.
- **`feat(backend): seed ofert do ręcznych testów (scripts/seed_listings.py)`**: bez niego ręczna kontrola UI z wynikami i podpowiedziami
  nie jest możliwa (0 wierszy w `listing`, brak `POST /listings/`). Poza briefem; osobny wpis.
- **`test(e2e): scenariusz filtrowania w Playwright`**: brief wymaga testów backendu i frontendu, nie e2e; do tego wymaga seeda. Osobny wpis.
- **`feat(frontend): synchronizacja filtrów z URL`** i **przyciski paginacji**: nie ma ich w briefie (D3). Osobne wpisy.
- **Wyszukiwanie odporne na wielkość liter z polskimi znakami** (np. `ł` → `Łódź`): SQLite `LIKE`/`lower()` składa tylko ASCII;
  poprawka wymaga kolumny znormalizowanej (migracja) albo funkcji SQL rejestrowanej w silniku. Osobny wpis; ryzyko opisane niżej.
- **`refactor(frontend): wydziel Locations.jsx z App.jsx`**: czysty move ok. 350 linii, ponad budżet; przełącznik widoku mieści się
  w 15 liniach bez tego. Osobny PR (jak w `listings.md`).
- **Cap `limit` i walidacja `Query` w `GET /locations/`**: zmiana istniejącego zachowania, brief jej nie żąda.

## Ryzyka i otwarte pytania

- SQLite `LIKE` jest case-insensitive tylko dla ASCII: `q=łó` nie znajdzie `Łódź`, a `order_by` sortuje binarnie (polskie litery po `z`).
- Kwoty są `Float`: porównania granic działają, ale wartości typu `499999.99999` mogą zaskoczyć na granicy; UI wysyła liczby całkowite lub z 2 miejscami.
- `package-lock.json` w kroku 6 przekroczy budżet linii, bo jest generowany; budżet dotyczy linii pisanych ręcznie.
- Czy oferty bez ceny/metrażu mają być widoczne przy aktywnym filtrze (D5)? Czy potrzebne „5+” pokoi (D9)?

## Strażnik zakresu

```bash
ALLOWED='^(README\.md|\.agent/plans/listing-filters\.md|services/backend/(main\.py|sql_app/schemas\.py|tests/conftest\.py|tests/api/test_listing(s|_filters|_suggestions)\.py|README\.md|CLAUDE\.md)|services/frontend/(package\.json|package-lock\.json|vite\.config\.js|README\.md|src/(api\.js|App\.jsx|App\.css|listingFilters(\.test)?\.js|Autocomplete(\.test)?\.jsx|ListingFilters(\.test)?\.jsx|ListingsView(\.test)?\.jsx)))$'
OUT=$(git diff --name-only af01bb8...HEAD | grep -vE "$ALLOWED")
[ -z "$OUT" ] || { echo "Pliki poza zakresem:"; echo "$OUT"; exit 1; }
```

## Protokół wykonania

```text
Wykonaj commit #N z .agent/plans/listing-filters.md. Tylko ten commit.
1. komenda weryfikacji z tabeli,
2. git diff --stat, strażnik zakresu,
3. zielone i w budżecie → commit z komunikatem z planu, git tag cp/N,
4. stop, czekaj na "dalej".
Odchylenie (nowy plik, >1.5× budżetu) → zgłoś, nie wykonuj.
```
