# VectorShelf Frontend

This is a Vite + React + Tailwind frontend for the Product Browser.

Quick start:

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Run dev server:

```bash
npm run dev
```

Environment:
- Copy `.env.example` to `.env.local` to configure `VITE_API_BASE_URL`. Default is `/api/v1`.

Notes:
- The Product Browser implements a product grid, category dropdown, Load More button and infinite scroll.
- API expectations: GET `${VITE_API_BASE_URL}/products` accepts `cursor`, `limit`, `category` and responds with `{ items: [], next_cursor, snapshot }`.
