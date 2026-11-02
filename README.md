# WineApp

A full-stack wine discovery app powered by **Wine-Searcher**, **Global Wine Score**, and **Spoonacular**.

## Features

- **Search** wines by name, producer, region, grape, vintage, and country
- **Wine detail** pages with scores, pricing, and food pairings
- **Compare** up to 4 wines side by side (score, price, value score, region, grapes)
- **Food pairing** lookup — enter a dish, get wine style recommendations
- **Cellar / Favorites** — authenticated users can save wines, add tasting notes, and rate bottles
- **Normalized internal DB** — providers are queried on cache miss, then persisted in PostgreSQL for fast reads

---

## Architecture

```
Frontend (Next.js + Tailwind)
       │
       ▼
Backend (FastAPI + Python)
  ├── search_service       ← searches DB first, falls back to Wine-Searcher
  ├── wine_service         ← upsert / enrich wine records
  ├── pairing_service      ← Spoonacular food-pairing integration
  ├── user_cellar_service  ← authenticated cellar management
  └── adapters/
       ├── WineSearcherAdapter     (search, identity, pricing)
       ├── GlobalWineScoreAdapter  (critic score enrichment)
       └── SpoonacularAdapter      (food pairing, dish lookup)
       ▼
PostgreSQL  (normalized wine, score, price, pairing, user tables)
Redis       (optional caching — read-through, configurable TTLs)
```

---

## Quick Start (Docker)

```bash
cp backend/.env.example backend/.env
# Add API keys to backend/.env

docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env` and set:

| Variable | Description |
|---|---|
| `WINE_SEARCHER_API_KEY` | Wine-Searcher API key |
| `GLOBAL_WINE_SCORE_API_KEY` | Global Wine Score API token |
| `SPOONACULAR_API_KEY` | Spoonacular API key |
| `SECRET_KEY` | JWT signing secret (change in production) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

---

## Backups

```bash
scripts/backup.sh                              # Saves to backups/, keeps the newest 14
scripts/restore.sh verify backups/FILE.dump    # Restores into a temporary database to prove it works
scripts/restore.sh replace backups/FILE.dump   # Replaces the live database, after asking you to confirm
```

Backups can hold seller financials. `backups/` is ignored by git, but copy them only to encrypted storage.

## Winery Acquisition Tool

`/wineries` and `/market` help screen licensed BC wineries as possible acquisitions. `/advisors` lists BC specialists to review a purchase; its entries are hand-checked and live in the page file. `/deals` tracks each purchase for the logged-in user; deal data, including seller financials, stays in the database and must never be committed.

Load or refresh the data from `backend/`, in this order:

```bash
python3 scripts/import_bc_wineries.py   # Licensed wineries, service capacity, endorsements
python3 scripts/import_bc_prices.py     # BC Liquor Store shelf prices (adds a monthly snapshot)
python3 scripts/import_listings.py      # Hand-entered sale listings: data/winery_listings.csv
python3 scripts/import_sales.py         # Hand-entered reported sales: data/winery_sales.csv
python3 scripts/check_land.py           # Map checks for wineries with a listing or deal; run after link_wineries.py
python3 scripts/import_market_stats.py  # Statistics Canada annual wine sales
python3 scripts/link_wineries.py        # Link wines and listings to wineries
```

Critic scores come from `scripts/seed_from_kaggle.py`.

To check whether listing pages still load and show the recorded price, run `python3 scripts/check_listings.py`. It respects `robots.txt` and only reports; add a new row to `data/winery_listings.csv` with today's `as_of` after confirming a listing by hand.

`link_wineries.py` only links exact name matches and confirmed aliases. It writes everything else to `data/winery_match_review.csv`. To confirm a match, add the name and licence number to `data/winery_aliases.csv` and run it again.

Public data doesn't show any winery's bottle sales or costs. Scores are a screening aid, and the estimate on each winery page runs on the user's own assumptions.

---

## Project Structure

```
wine-app/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI route handlers
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic (search, wine, pairing, cellar, auth)
│   │   ├── adapters/           # External provider adapters
│   │   ├── db/                 # DB session + base
│   │   ├── core/               # Config, security, logging
│   │   └── jobs/               # Background refresh jobs
│   ├── alembic/                # Database migrations
│   ├── tests/unit/             # Unit tests (all mocked, no DB/network)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       ├── components/         # UI components (WineCard, SearchBar, etc.)
│       ├── lib/                # API client, utilities
│       └── types/              # TypeScript type definitions
└── docker-compose.yml
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/wines/search` | Search wines with filters |
| `GET` | `/api/v1/wines/:id` | Wine detail |
| `GET` | `/api/v1/wines/:id/scores` | Score data |
| `GET` | `/api/v1/wines/:id/prices` | Price summary |
| `POST` | `/api/v1/wines/compare` | Compare 2–4 wines |
| `GET` | `/api/v1/pairings?food=steak` | Food-wine pairing |
| `GET` | `/api/v1/users/me/cellar` | List saved wines |
| `POST` | `/api/v1/users/me/cellar` | Add wine to cellar |
| `PATCH` | `/api/v1/users/me/cellar/:wine_id` | Update notes/rating |
| `DELETE` | `/api/v1/users/me/cellar/:wine_id` | Remove from cellar |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/login` | Login (returns JWT) |

---

## Running Tests

```bash
cd backend
python3 -m pytest tests/unit/ -v
```

---

## Data Sources

- **Wine-Searcher** — wine identity, search, and pricing
- **Global Wine Score** — normalized critic score aggregation
- **Spoonacular** — food-wine pairing recommendations

Provider API keys are stored server-side only and never exposed to the frontend.
