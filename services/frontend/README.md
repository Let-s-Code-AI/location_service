# Frontend

Simple web UI for the [monorepo](../../README.md), built with **React + Vite** (JavaScript). It manages `Location` records (list, add, delete) and has a **Oferty** view that lists listings with filters: price, price per m² and area ranges, number of rooms, city and district with autocomplete, a live result count and a reset button.

## Requirements

- Node.js 20.19+ (or 22+)
- the backend running (see [`../backend`](../backend)), by default at `http://127.0.0.1:8000`

## Run

```bash
cd services/frontend
npm install
npm run dev        # http://localhost:5173
```

Other scripts: `npm run build` (production bundle in `dist/`), `npm run preview`.

## Tests

```bash
npm test           # Vitest + Testing Library in jsdom, single run
```

Test files sit next to the code (`src/*.test.js`, `src/*.test.jsx`). Components get their data through props or a mocked `./api.js`, so the tests do not need a running backend.

## Backend connection

The backend has no CORS configured, so the dev server proxies `/api/*` to the backend (the `/api` prefix is stripped). To use a different backend address:

```bash
BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

The API client lives in `src/api.js`.

## Structure

```
index.html
vite.config.js      # React plugin, /api proxy, Vitest config
src/
├── main.jsx        # entry point
├── App.jsx         # view switch + locations list and add form
├── ListingsView.jsx    # listings view: filter state, debounced fetch, table
├── ListingFilters.jsx  # filter panel: ranges, rooms, autocomplete, count, reset
├── Autocomplete.jsx    # combobox with debounced suggestions and keyboard support
├── listingFilters.js   # filter model: validation, query string, Polish plurals
├── api.js          # fetch wrapper for the backend
├── ui.jsx          # shared icons and form field
└── App.css
```
