# Frontend

Simple web UI for the [monorepo](../../README.md), built with **React + Vite** (JavaScript). It currently manages `Location` records (list, add, delete) – the only CRUD implemented in the backend so far.

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

## Backend connection

The backend has no CORS configured, so the dev server proxies `/api/*` to the backend (the `/api` prefix is stripped). To use a different backend address:

```bash
BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

The API client lives in `src/api.js`.

## Structure

```
index.html
vite.config.js      # React plugin + /api proxy
src/
├── main.jsx        # entry point
├── App.jsx         # view switch (Lokalizacje / Ogłoszenia), locations list + add form
├── Listings.jsx    # listings search: phrase, price and rooms filters (debounced GET /listings/)
├── ui.jsx          # shared Icon and Field components
├── api.js          # fetch wrapper for the backend
└── App.css
```
