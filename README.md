# VectorShelf (local dev)

This repository contains a FastAPI backend and a React frontend for browsing products.

Quick start (development):

Backend (uses SQLite fallback if PostgreSQL not available):

```powershell
cd backend
# Option A: use local SQLite (dev.db)
$env:DATABASE_URL = 'sqlite:///./dev.db'
$env:APP_NAME = 'Product Browser API (SQLite Dev)'
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Option B: use PostgreSQL
# set DATABASE_URL in backend/.env or environment
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend (Vite):

```powershell
cd frontend
npm install
npm run dev
# Open http://localhost:5174
```

Seeding (Postgres only):

```powershell
cd backend
# ensure DATABASE_URL points to Postgres
python scripts/seed_database.py
```

Endpoints:
- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:5174

Features:
- Cursor-based pagination (updated_at DESC, id DESC)
- Snapshot consistency to avoid duplicates/misses while browsing
- Category filtering

