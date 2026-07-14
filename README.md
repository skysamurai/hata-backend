# Hata — Real Estate Listing Parser & Filter

Backend service for parsing real estate listings, phone number extraction, and AI-powered listing filtering.

## Key Technical Features

- **Async SQLAlchemy 2.0:** DeclarativeBase, Mapped[], async_sessionmaker, Alembic migrations
- **Celery task queue:** Redis broker, background parsing tasks with status polling
- **AI filtering:** DeepSeek-powered listing quality scoring and duplicate detection
- **FastAPI REST API:** 4 routers (listings, regions, parser, stats)
- **Phone parsing:** pattern-based phone number extraction and blacklist filtering

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Pydantic |
| ORM | SQLAlchemy 2.0 (async, DeclarativeBase, Mapped[]) |
| DB | PostgreSQL + asyncpg |
| Migrations | Alembic (async engine) |
| Task Queue | Celery + Redis |
| AI | DeepSeek API |
| Frontend | React + TypeScript + Vite |

## Architecture

```
FastAPI API ──→ SQLAlchemy 2.0 Async ──→ PostgreSQL
     │
     ├── Celery Worker (Redis broker)
     │     └── Parser Tasks
     │
     └── AI Filter (DeepSeek)
           └── Listing Quality Scoring
```

## Models

- `Listing` — real estate listing with price, location, specs
- `PhoneDef` — phone number prefix definitions
- `PhoneStat` — phone number statistics
- `ParseTask` — background parsing task tracking
- `Region` — geographic regions
- `Blacklist` — phone number blacklist

## Quick Start

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
