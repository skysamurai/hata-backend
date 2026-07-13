# Hata Frontend Design Spec

**Date:** 2026-07-13
**Status:** Approved
**Epic:** Hata-xvk

## Overview

Single-page web interface for Hata — a real estate listing aggregator. Backend API is ready (FastAPI). Frontend: React 19 + TypeScript 6 + Vite 8.

## Architecture

```
App
├── FilterBar        — collapsible filter panel (region, rooms, price range, metro, source, is_agent)
├── ListingFeed      — compact table-like feed of listing rows
├── ListingModal     — detail view (opens on row click)
├── StatsWidget      — sidebar: total, agent/private counts, new today, per-source
├── ParseWidget      — sidebar: start parse buttons, last task status
└── useApi hook      — fetch wrapper for all API calls
```

Single page, no router needed. State lifted to App.

## Component Tree & Data Flow

```
App (state: filters, listings[], stats, selectedListing)
├── Header (logo + active filter summary)
├── Main layout (flex row)
│   ├── Left (flex: 1)
│   │   ├── FilterBar
│   │   │   └── collapsible panel with: RegionSelect, RoomsSelect, PriceRange, MetroInput, SourceSelect, IsAgentToggle
│   │   └── ListingFeed
│   │       └── ListingRow[] (compact single-row cards)
│   └── Right (280px, flex-shrink: 0)
│       ├── StatsWidget
│       └── ParseWidget
└── ListingModal (conditional, portal to body)
```

**Data flow:**
1. App fetches `/api/regions` on mount → populates RegionSelect
2. Filter changes → debounce 300ms → `GET /api/listings?...` + `GET /api/stats?...`
3. Row click → `GET /api/listings/:id` → show ListingModal
4. Parse button → `POST /api/parse/start` → poll `GET /api/parse/status/:task_id`

## Components Detail

### FilterBar
- **Collapsed state:** single line showing active filters summary (e.g. "СПб · 1-2к · 5-15M · Собственники")
- **Expanded state:** form fields in 1-2 rows
- Toggle: click on summary or chevron icon
- All changes apply automatically with 300ms debounce on text inputs
- Fields: RegionSelect (from /api/regions), RoomsSelect (1,2,3,4+), PriceMin, PriceMax, Metro (text), SourceSelect (avito/cian/all), IsAgentToggle (checkbox: "Только собственники")

### ListingFeed
- Compact table rows: `[rooms+area] [price] [region+metro] [agent badge] [time ago]`
- Agent badge: green "👤 Частное" / red "🤖 Агент N" where N = agent_score
- Click row → ListingModal
- Pagination at bottom: page numbers, prev/next

### ListingModal
- Overlay + centered card (max-width 600px)
- Fields: rooms, area, price, address, metro, floor/total_floors, phone, description, source link, agent_score bar
- Dismiss: × button, click outside, Escape key
- Fetch details from `/api/listings/:id` on open

### StatsWidget
- Card with title "📊 Статистика"
- Rows: Всего, Собственники, Агенты, Новых сегодня
- Per-source: Авито N, Циан N
- Updates on every filter change

### ParseWidget
- Card with title "⚙ Парсинг"
- Two buttons: "▶ Запустить Авито", "▶ Запустить Циан"
- Below buttons: last task status (idle / running / done with count / error)
- Poll `/api/parse/status/:task_id` every 2s while task is running

## Theme
- System preference via `prefers-color-scheme` media query
- CSS custom properties for colors, no runtime theme toggle needed
- Light: white bg, dark text, subtle borders
- Dark: #1a1a1a bg, light text, darker borders

## Error Handling
- Network errors: toast notification in bottom-right corner
- Empty state: "Нет объявлений" with suggestion to change filters
- Loading state: skeleton rows while fetching

## Non-Goals
- No router (single page)
- No state management library (React useState/useEffect sufficient)
- No UI component library (plain CSS)
- No authentication
- No SSR/SSG
- No mobile-first design (desktop-first, responsive as stretch goal)
