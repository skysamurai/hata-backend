# Hata — Парсер аренды недвижимости

## Overview
Веб-приложение для парсинга объявлений аренды квартир и комнат с Avito и Cian.
Автоматическое отсеивание риэлторов (5-слойный детектор). Все регионы РФ, первый регион — Казань.

## Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | Python 3.12 + FastAPI |
| Parsers | Playwright + httpx |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis + Celery |
| Deploy | Docker Compose |

## Database Models
- **regions**: id, name, avito_location_id, cian_region_id, parent_id
- **phone_defs**: prefix, range_start, range_end, operator, region (DEF-code → region mapping)
- **listings**: source, external_id, url, title, price, address, metro, rooms, area, floor, description, phone_raw, phone_formatted, phone_region, region_id, is_agent, agent_score, first_seen, last_seen, is_active
- **phone_stats**: phone_hash, count_listings, count_sources, regions[], last_seen
- **blacklist**: phone_hash, comment, added_at
- **parse_tasks**: region_id, source, status, started_at, listings_found, listings_new

## Realtor Detection (5 layers)
1. API filter: `privateOnly=1` / `user=1` on Avito, `source=owner` on Cian
2. Frequency: phone in 1 listing = 0, 2-3 = 20, 4-10 = 50, 11+ = 90
3. Regional: DEF mismatch with listing region → +30 to score
4. Cross-platform: phone found on both Avito AND Cian → +25
5. Blacklist: manual phone ban → score = 100

Threshold: `is_agent = agent_score >= 60`

## API Endpoints
- `GET /api/regions` — list regions
- `GET /api/listings` — listings with filters and pagination
- `GET /api/listings/:id` — listing detail
- `POST /api/parse/start` — start parsing for region
- `GET /api/parse/status/:task_id` — task status
- `GET /api/stats` — statistics
- `POST /api/blacklist` — add to blacklist

## Data Flow
Celery Beat → Parser (Playwright/httpx) → RealtorDetector (5 layers) → PostgreSQL → WebSocket → Frontend
