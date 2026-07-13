# Hata Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build single-page web interface for Hata real estate aggregator with listing feed, filters, modal details, stats, and parse controls.

**Architecture:** React 19 + TypeScript 6 + Vite 8. Single page, no router. State lifted to App. Plain CSS with system theme (prefers-color-scheme). API via fetch with 300ms debounced filter auto-apply.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Vitest + @testing-library/react for TDD

---

## File Map

| File | Responsibility |
|------|---------------|
| `frontend/src/types.ts` | Shared TS interfaces (Listing, Stats, Region, ParseTask) |
| `frontend/src/api.ts` | Fetch wrapper, all API calls, typed responses |
| `frontend/src/components/FilterBar.tsx` | Collapsible filter panel (region, rooms, price, metro, source, is_agent) |
| `frontend/src/components/ListingFeed.tsx` | Compact table rows with pagination |
| `frontend/src/components/ListingModal.tsx` | Detail modal overlay |
| `frontend/src/components/StatsWidget.tsx` | Statistics card |
| `frontend/src/components/ParseWidget.tsx` | Parse trigger buttons + status |
| `frontend/src/App.tsx` | **Modify** — main layout, state hub, compose all components |
| `frontend/src/index.css` | **Modify** — CSS variables, theme (light/dark), base styles |
| `frontend/src/App.css` | **Modify** — component layout styles |

---

### Task 0: Test Infrastructure

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Install vitest and testing-library**

Run: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`

- [ ] **Step 2: Add test script and vitest config to package.json**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

- [ ] **Step 3: Add vitest config to vite.config.ts**

```ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
```

- [ ] **Step 4: Create test setup file**

```ts
// frontend/src/test/setup.ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 5: Verify test infrastructure works**

Run: `cd frontend && npx vitest run`
Expected: "No test files found" (infra works, just no tests yet)

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/test/
git commit -m "chore: add vitest and testing-library for TDD"
```

---

### Task 1: Types + API Client

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/api.test.ts`

- [ ] **Step 1: Write failing test for types and API**

```ts
// frontend/src/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'

// We'll test that fetch is called with correct URL and params
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
})

describe('fetchListings', () => {
  it('builds URL with all filter params', async () => {
    const { fetchListings } = await import('./api')
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 50 })
    } as Response)

    await fetchListings({ region_id: 1, rooms: 2, price_min: 5000000, is_agent: false, page: 1 })

    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('region_id=1')
    expect(url).toContain('rooms=2')
    expect(url).toContain('price_min=5000000')
    expect(url).toContain('is_agent=false')
    expect(url).toContain('page=1')
    expect(url).toContain('per_page=50')
  })
})

describe('fetchStats', () => {
  it('fetches stats for a region', async () => {
    const { fetchStats } = await import('./api')
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ total: 100, agent_count: 30, private_count: 70, new_today: 5, by_source: { avito: 60, cian: 40 } })
    } as Response)

    const stats = await fetchStats(1)
    expect(stats.total).toBe(100)
    expect(mockFetch.mock.calls[0][0]).toContain('region_id=1')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/api.test.ts`
Expected: FAIL — `fetchListings` and `fetchStats` not exported

- [ ] **Step 3: Create types.ts**

```ts
// frontend/src/types.ts
export interface Listing {
  id: number
  source: 'avito' | 'cian'
  external_id: string
  url: string
  title: string
  price: number | null
  address: string | null
  metro: string | null
  rooms: number | null
  area: number | null
  floor: number | null
  total_floors: number | null
  description: string | null
  phone_raw: string | null
  phone_formatted: string | null
  region_id: number
  is_agent: boolean
  agent_score: number
  first_seen: string
  last_seen: string
}

export interface ListingFilters {
  region_id?: number
  rooms?: number
  price_min?: number
  price_max?: number
  metro?: string
  source?: string
  is_agent?: boolean
  page?: number
  per_page?: number
}

export interface ListingsResponse {
  items: Listing[]
  total: number
  page: number
  per_page: number
}

export interface Stats {
  total: number
  agent_count: number
  private_count: number
  new_today: number
  by_source: { avito: number; cian: number }
}

export interface Region {
  id: number
  name: string
  code: string
}

export interface ParseTask {
  id: number
  task_id: string
  region_id: number
  source: string
  status: string
  started_at: string | null
  finished_at: string | null
  listings_found: number | null
}

export interface ParseStatus {
  task_id: string
  status: string
  result?: unknown
}
```

- [ ] **Step 4: Create api.ts**

```ts
// frontend/src/api.ts
import type { Listing, ListingFilters, ListingsResponse, Stats, Region, ParseTask, ParseStatus } from './types'

const BASE = '/api'

async function get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') url.searchParams.set(k, String(v))
    })
  }
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string, body?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin)
  const formData = new URLSearchParams()
  if (body) {
    Object.entries(body).forEach(([k, v]) => {
      if (v !== undefined) formData.set(k, String(v))
    })
  }
  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json()
}

export function fetchListings(filters: ListingFilters): Promise<ListingsResponse> {
  const params: Record<string, string | number | boolean> = {}
  if (filters.region_id) params.region_id = filters.region_id
  if (filters.rooms !== undefined) params.rooms = filters.rooms
  if (filters.price_min !== undefined) params.price_min = filters.price_min
  if (filters.price_max !== undefined) params.price_max = filters.price_max
  if (filters.metro) params.metro = filters.metro
  if (filters.source) params.source = filters.source
  if (filters.is_agent !== undefined) params.is_agent = filters.is_agent
  params.page = filters.page ?? 1
  params.per_page = filters.per_page ?? 50
  return get<ListingsResponse>(`${BASE}/listings`, params)
}

export function fetchListing(id: number): Promise<Listing> {
  return get<Listing>(`${BASE}/listings/${id}`)
}

export function fetchRegions(): Promise<Region[]> {
  return get<Region[]>(`${BASE}/regions`)
}

export function fetchStats(regionId?: number): Promise<Stats> {
  return get<Stats>(`${BASE}/stats`, { region_id: regionId })
}

export function startParse(regionId: number, source: string): Promise<{ task_id: string; status: string }> {
  return post(`${BASE}/parse/start`, { region_id: regionId, source })
}

export function fetchParseStatus(taskId: string): Promise<ParseStatus> {
  return get<ParseStatus>(`${BASE}/parse/status/${taskId}`)
}

export function fetchParseHistory(regionId?: number, limit?: number): Promise<ParseTask[]> {
  const params: Record<string, string | number> = { limit: limit ?? 50 }
  if (regionId) params.region_id = regionId
  return get<ParseTask[]>(`${BASE}/parse/history`, params)
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/api.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/api.test.ts
git commit -m "feat: add types and API client with tests"
```

---

### Task 2: FilterBar Component

**Files:**
- Create: `frontend/src/components/FilterBar.tsx`
- Create: `frontend/src/components/FilterBar.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/src/components/FilterBar.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterBar } from './FilterBar'
import type { Region } from '../types'

const mockRegions: Region[] = [
  { id: 1, name: 'Санкт-Петербург', code: 'spb' },
  { id: 2, name: 'Москва', code: 'msk' },
]

describe('FilterBar', () => {
  it('renders collapsed summary with active filters', () => {
    render(
      <FilterBar
        regions={mockRegions}
        filters={{ region_id: 1, rooms: 2, is_agent: false }}
        onChange={vi.fn()}
      />
    )
    // Should show active filter summary text
    expect(screen.getByText(/Санкт-Петербург/)).toBeDefined()
    expect(screen.getByText(/собственник/i)).toBeDefined()
  })

  it('expands on click and shows all filter fields', async () => {
    const user = userEvent.setup()
    render(
      <FilterBar
        regions={mockRegions}
        filters={{}}
        onChange={vi.fn()}
      />
    )
    const toggle = screen.getByRole('button', { name: /фильтры/i })
    await user.click(toggle)
    // After expand, should see region select
    expect(screen.getByRole('combobox', { name: /регион/i })).toBeDefined()
  })

  it('calls onChange when region is selected', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(
      <FilterBar
        regions={mockRegions}
        filters={{}}
        onChange={onChange}
      />
    )
    // Expand first
    await user.click(screen.getByRole('button', { name: /фильтры/i }))
    // Select region
    const regionSelect = screen.getByRole('combobox', { name: /регион/i })
    await user.selectOptions(regionSelect, '1')
    expect(onChange).toHaveBeenCalledWith({ region_id: 1 })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/FilterBar.test.tsx`
Expected: FAIL — FilterBar not exported

- [ ] **Step 3: Write FilterBar component**

```tsx
// frontend/src/components/FilterBar.tsx
import { useState } from 'react'
import type { Region, ListingFilters } from '../types'

interface FilterBarProps {
  regions: Region[]
  filters: ListingFilters
  onChange: (filters: Partial<ListingFilters>) => void
}

function filterSummary(regions: Region[], filters: ListingFilters): string {
  const parts: string[] = []
  if (filters.region_id) {
    const r = regions.find(reg => reg.id === filters.region_id)
    if (r) parts.push(r.name)
  }
  if (filters.rooms !== undefined) {
    parts.push(filters.rooms >= 4 ? `${filters.rooms}+к` : `${filters.rooms}к`)
  }
  if (filters.price_min || filters.price_max) {
    const min = filters.price_min ? `${(filters.price_min / 1_000_000).toFixed(0)}M` : ''
    const max = filters.price_max ? `${(filters.price_max / 1_000_000).toFixed(0)}M` : ''
    parts.push(`${min}–${max} ₽`)
  }
  if (filters.metro) parts.push(`м. ${filters.metro}`)
  if (filters.source) parts.push(filters.source === 'avito' ? 'Авито' : 'Циан')
  if (filters.is_agent === false) parts.push('Собственники')
  return parts.length > 0 ? parts.join(' · ') : 'Все объявления'
}

export function FilterBar({ regions, filters, onChange }: FilterBarProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="filter-bar">
      <button
        className="filter-summary"
        onClick={() => setExpanded(!expanded)}
        aria-label="Фильтры"
      >
        <span>{filterSummary(regions, filters)}</span>
        <span className="filter-chevron">{expanded ? '▴' : '▾'}</span>
      </button>

      {expanded && (
        <div className="filter-panel">
          <label>
            Регион
            <select
              aria-label="Регион"
              value={filters.region_id ?? ''}
              onChange={e => onChange({ region_id: e.target.value ? Number(e.target.value) : undefined })}
            >
              <option value="">Все регионы</option>
              {regions.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </label>

          <label>
            Комнат
            <select
              aria-label="Комнат"
              value={filters.rooms ?? ''}
              onChange={e => onChange({ rooms: e.target.value ? Number(e.target.value) : undefined })}
            >
              <option value="">Любая</option>
              <option value="0">Студия</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4+</option>
            </select>
          </label>

          <label>
            Цена от
            <input
              type="number"
              placeholder="0"
              value={filters.price_min ?? ''}
              onChange={e => onChange({ price_min: e.target.value ? Number(e.target.value) : undefined })}
            />
          </label>

          <label>
            Цена до
            <input
              type="number"
              placeholder="Любая"
              value={filters.price_max ?? ''}
              onChange={e => onChange({ price_max: e.target.value ? Number(e.target.value) : undefined })}
            />
          </label>

          <label>
            Метро
            <input
              type="text"
              placeholder="Название станции"
              value={filters.metro ?? ''}
              onChange={e => onChange({ metro: e.target.value || undefined })}
            />
          </label>

          <label>
            Источник
            <select
              aria-label="Источник"
              value={filters.source ?? ''}
              onChange={e => onChange({ source: e.target.value || undefined })}
            >
              <option value="">Все</option>
              <option value="avito">Авито</option>
              <option value="cian">Циан</option>
            </select>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.is_agent === false}
              onChange={e => onChange({ is_agent: e.target.checked ? false : undefined })}
            />
            Только собственники
          </label>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/FilterBar.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/FilterBar.tsx frontend/src/components/FilterBar.test.tsx
git commit -m "feat: add FilterBar component with collapsible panel"
```

---

### Task 3: ListingFeed Component

**Files:**
- Create: `frontend/src/components/ListingFeed.tsx`
- Create: `frontend/src/components/ListingFeed.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/src/components/ListingFeed.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ListingFeed } from './ListingFeed'
import type { Listing } from '../types'

const mockListings: Listing[] = [
  {
    id: 1, source: 'avito', external_id: 'ext1', url: 'https://...',
    title: '2-к квартира', price: 12000000, address: 'СПб', metro: 'Приморская',
    rooms: 2, area: 65, floor: 5, total_floors: 12, description: '',
    phone_raw: '+79111234567', phone_formatted: '+79111234567',
    region_id: 1, is_agent: false, agent_score: 0,
    first_seen: '2026-07-13T00:00:00', last_seen: '2026-07-13T00:00:00',
  },
  {
    id: 2, source: 'cian', external_id: 'ext2', url: 'https://...',
    title: '1-к квартира', price: 7500000, address: 'Мск', metro: 'Южная',
    rooms: 1, area: 38, floor: 3, total_floors: 9, description: '',
    phone_raw: null, phone_formatted: null,
    region_id: 2, is_agent: true, agent_score: 70,
    first_seen: '2026-07-13T00:00:00', last_seen: '2026-07-13T00:00:00',
  },
]

describe('ListingFeed', () => {
  it('renders listing rows', () => {
    render(
      <ListingFeed
        listings={mockListings}
        total={2}
        page={1}
        perPage={50}
        onPageChange={vi.fn()}
        onListingClick={vi.fn()}
      />
    )
    expect(screen.getByText(/2-к, 65 м²/)).toBeDefined()
    expect(screen.getByText(/12 000 000 ₽/)).toBeDefined()
    expect(screen.getByText(/1-к, 38 м²/)).toBeDefined()
    expect(screen.getByText(/7 500 000 ₽/)).toBeDefined()
  })

  it('shows private badge for non-agent listings', () => {
    render(
      <ListingFeed
        listings={mockListings} total={2} page={1} perPage={50}
        onPageChange={vi.fn()} onListingClick={vi.fn()}
      />
    )
    expect(screen.getByText('Частное')).toBeDefined()
  })

  it('shows agent badge with score', () => {
    render(
      <ListingFeed
        listings={mockListings} total={2} page={1} perPage={50}
        onPageChange={vi.fn()} onListingClick={vi.fn()}
      />
    )
    expect(screen.getByText('Агент 70')).toBeDefined()
  })

  it('calls onListingClick when row is clicked', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(
      <ListingFeed
        listings={mockListings} total={2} page={1} perPage={50}
        onPageChange={vi.fn()} onListingClick={onClick}
      />
    )
    await user.click(screen.getByText(/2-к, 65 м²/))
    expect(onClick).toHaveBeenCalledWith(1)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/ListingFeed.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write ListingFeed component**

```tsx
// frontend/src/components/ListingFeed.tsx
import type { Listing } from '../types'

interface ListingFeedProps {
  listings: Listing[]
  total: number
  page: number
  perPage: number
  onPageChange: (page: number) => void
  onListingClick: (id: number) => void
}

function priceStr(price: number | null): string {
  if (price == null) return '—'
  return price.toLocaleString('ru-RU') + ' ₽'
}

function roomsStr(r: number | null): string {
  if (r == null) return '—'
  if (r === 0) return 'Студия'
  return `${r}-к`
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} мин`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} ч`
  return `${Math.floor(hours / 24)} д`
}

export function ListingFeed({ listings, total, page, perPage, onPageChange, onListingClick }: ListingFeedProps) {
  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="listing-feed">
      {listings.length === 0 ? (
        <div className="empty-state">Нет объявлений. Измените фильтры.</div>
      ) : (
        <>
          <div className="listing-rows">
            {listings.map(l => (
              <div
                key={l.id}
                className="listing-row"
                onClick={() => onListingClick(l.id)}
                role="button"
                tabIndex={0}
                onKeyDown={e => { if (e.key === 'Enter') onListingClick(l.id) }}
              >
                <span className="listing-rooms">{roomsStr(l.rooms)}, {l.area} м²</span>
                <span className="listing-price">{priceStr(l.price)}</span>
                <span className="listing-location">📍 {l.address}{l.metro ? `, м. ${l.metro}` : ''}</span>
                <span className={`listing-badge ${l.is_agent ? 'agent' : 'private'}`}>
                  {l.is_agent ? `Агент ${l.agent_score}` : 'Частное'}
                </span>
                <span className="listing-time">{timeAgo(l.last_seen)}</span>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>←</button>
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                const p = i + 1
                return (
                  <button
                    key={p}
                    className={p === page ? 'active' : ''}
                    onClick={() => onPageChange(p)}
                  >
                    {p}
                  </button>
                )
              })}
              <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>→</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/ListingFeed.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ListingFeed.tsx frontend/src/components/ListingFeed.test.tsx
git commit -m "feat: add ListingFeed with compact rows and pagination"
```

---

### Task 4: ListingModal Component

**Files:**
- Create: `frontend/src/components/ListingModal.tsx`
- Create: `frontend/src/components/ListingModal.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/src/components/ListingModal.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ListingModal } from './ListingModal'
import type { Listing } from '../types'

const mockListing: Listing = {
  id: 1, source: 'avito', external_id: 'ext1', url: 'https://avito.ru/123',
  title: '2-к квартира, 65 м²', price: 12000000,
  address: 'Санкт-Петербург', metro: 'Приморская',
  rooms: 2, area: 65, floor: 5, total_floors: 12,
  description: 'Хорошая квартира с видом на залив',
  phone_raw: '+7 (911) 123-45-67', phone_formatted: '+79111234567',
  region_id: 1, is_agent: false, agent_score: 0,
  first_seen: '2026-07-13T00:00:00', last_seen: '2026-07-13T00:00:00',
}

describe('ListingModal', () => {
  it('renders listing details', () => {
    render(<ListingModal listing={mockListing} onClose={vi.fn()} />)
    expect(screen.getByText(/2-к квартира, 65 м²/)).toBeDefined()
    expect(screen.getByText(/12 000 000 ₽/)).toBeDefined()
    expect(screen.getByText(/Санкт-Петербург/)).toBeDefined()
    expect(screen.getByText(/Приморская/)).toBeDefined()
    expect(screen.getByText(/5\/12/)).toBeDefined()
  })

  it('calls onClose on × button click', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<ListingModal listing={mockListing} onClose={onClose} />)
    await user.click(screen.getByRole('button', { name: /закрыть/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose on overlay click', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<ListingModal listing={mockListing} onClose={onClose} />)
    await user.click(screen.getByTestId('modal-overlay'))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose on Escape', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<ListingModal listing={mockListing} onClose={onClose} />)
    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/ListingModal.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write ListingModal component**

```tsx
// frontend/src/components/ListingModal.tsx
import { useEffect } from 'react'
import type { Listing } from '../types'

interface ListingModalProps {
  listing: Listing
  onClose: () => void
}

function priceStr(price: number | null): string {
  if (price == null) return '—'
  return price.toLocaleString('ru-RU') + ' ₽'
}

export function ListingModal({ listing, onClose }: ListingModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="modal-overlay"
      data-testid="modal-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="modal-card">
        <div className="modal-header">
          <h2>{listing.title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">✕</button>
        </div>

        <div className="modal-body">
          <div className="modal-price">{priceStr(listing.price)}</div>

          <div className="modal-fields">
            <div className="modal-field">
              <span className="field-label">Адрес</span>
              <span>{listing.address || '—'}</span>
            </div>
            {listing.metro && (
              <div className="modal-field">
                <span className="field-label">Метро</span>
                <span>{listing.metro}</span>
              </div>
            )}
            <div className="modal-field">
              <span className="field-label">Комнат</span>
              <span>{listing.rooms != null ? (listing.rooms === 0 ? 'Студия' : listing.rooms) : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Площадь</span>
              <span>{listing.area ? `${listing.area} м²` : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Этаж</span>
              <span>{listing.floor != null && listing.total_floors != null ? `${listing.floor}/${listing.total_floors}` : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Телефон</span>
              <span>{listing.phone_raw || listing.phone_formatted || '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Источник</span>
              <span>{listing.source === 'avito' ? 'Авито' : 'Циан'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Статус</span>
              <span className={listing.is_agent ? 'text-agent' : 'text-private'}>
                {listing.is_agent ? `🤖 Агент (score: ${listing.agent_score})` : '👤 Частное лицо'}
              </span>
            </div>
          </div>

          {listing.description && (
            <div className="modal-description">
              <div className="field-label">Описание</div>
              <p>{listing.description}</p>
            </div>
          )}

          <a href={listing.url} target="_blank" rel="noopener noreferrer" className="modal-link">
            Открыть оригинал объявления →
          </a>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/ListingModal.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ListingModal.tsx frontend/src/components/ListingModal.test.tsx
git commit -m "feat: add ListingModal with overlay and keyboard dismiss"
```

---

### Task 5: StatsWidget + ParseWidget

**Files:**
- Create: `frontend/src/components/StatsWidget.tsx`
- Create: `frontend/src/components/StatsWidget.test.tsx`
- Create: `frontend/src/components/ParseWidget.tsx`
- Create: `frontend/src/components/ParseWidget.test.tsx`

- [ ] **Step 1: Write failing tests for both widgets**

```tsx
// frontend/src/components/StatsWidget.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatsWidget } from './StatsWidget'
import type { Stats } from '../types'

const mockStats: Stats = {
  total: 342,
  agent_count: 144,
  private_count: 198,
  new_today: 15,
  by_source: { avito: 201, cian: 141 },
}

describe('StatsWidget', () => {
  it('renders all stat values', () => {
    render(<StatsWidget stats={mockStats} />)
    expect(screen.getByText('342')).toBeDefined()
    expect(screen.getByText('198')).toBeDefined()
    expect(screen.getByText('144')).toBeDefined()
    expect(screen.getByText('15')).toBeDefined()
    expect(screen.getByText('201')).toBeDefined()
    expect(screen.getByText('141')).toBeDefined()
  })

  it('renders placeholder when stats is null', () => {
    render(<StatsWidget stats={null} />)
    expect(screen.getByText('—')).toBeDefined()
  })
})
```

```tsx
// frontend/src/components/ParseWidget.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ParseWidget } from './ParseWidget'

describe('ParseWidget', () => {
  it('renders parse buttons for avito and cian', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={null} />)
    expect(screen.getByRole('button', { name: /авито/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /циан/i })).toBeDefined()
  })

  it('calls onStartParse with correct source', async () => {
    const onStart = vi.fn()
    const user = userEvent.setup()
    render(<ParseWidget onStartParse={onStart} lastStatus={null} />)
    await user.click(screen.getByRole('button', { name: /авито/i }))
    expect(onStart).toHaveBeenCalledWith('avito')
  })

  it('shows running status when task is pending', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={{ task_id: 't1', status: 'PENDING' }} />)
    expect(screen.getByText(/выполняется/i)).toBeDefined()
  })

  it('shows done status with result', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={{ task_id: 't2', status: 'SUCCESS', result: { listings_found: 42 } }} />)
    expect(screen.getByText(/завершён/)).toBeDefined()
    expect(screen.getByText(/42/)).toBeDefined()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/StatsWidget.test.tsx src/components/ParseWidget.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write StatsWidget**

```tsx
// frontend/src/components/StatsWidget.tsx
import type { Stats } from '../types'

interface StatsWidgetProps {
  stats: Stats | null
}

export function StatsWidget({ stats }: StatsWidgetProps) {
  return (
    <div className="widget stats-widget">
      <h3>📊 Статистика</h3>
      <div className="stat-row">
        <span>Всего</span>
        <b>{stats?.total ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>👤 Собственники</span>
        <b>{stats?.private_count ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>🤖 Агенты</span>
        <b>{stats?.agent_count ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>🆕 Сегодня</span>
        <b>{stats?.new_today ?? '—'}</b>
      </div>
      <div className="stat-divider" />
      <div className="stat-row">
        <span>Авито</span>
        <b>{stats?.by_source.avito ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>Циан</span>
        <b>{stats?.by_source.cian ?? '—'}</b>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Write ParseWidget**

```tsx
// frontend/src/components/ParseWidget.tsx
import type { ParseStatus } from '../types'

interface ParseWidgetProps {
  onStartParse: (source: string) => void
  lastStatus: ParseStatus | null
}

function statusText(status: ParseStatus | null): string {
  if (!status) return 'Готов к запуску'
  switch (status.status) {
    case 'PENDING':
    case 'STARTED':
      return '⏳ Выполняется...'
    case 'SUCCESS': {
      const count = (status.result as Record<string, unknown>)?.listings_found ?? '?'
      return `✓ Завершён (найдено: ${count})`
    }
    case 'FAILURE':
      return '✗ Ошибка'
    default:
      return `Статус: ${status.status}`
  }
}

export function ParseWidget({ onStartParse, lastStatus }: ParseWidgetProps) {
  return (
    <div className="widget parse-widget">
      <h3>⚙ Парсинг</h3>
      <button className="parse-btn" onClick={() => onStartParse('avito')}>
        ▶ Запустить Авито
      </button>
      <button className="parse-btn" onClick={() => onStartParse('cian')}>
        ▶ Запустить Циан
      </button>
      <div className="parse-status">{statusText(lastStatus)}</div>
    </div>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/StatsWidget.test.tsx src/components/ParseWidget.test.tsx`
Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/StatsWidget.tsx frontend/src/components/StatsWidget.test.tsx frontend/src/components/ParseWidget.tsx frontend/src/components/ParseWidget.test.tsx
git commit -m "feat: add StatsWidget and ParseWidget components"
```

---

### Task 6: App Integration + Styles

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/App.css`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing integration test**

```tsx
// frontend/src/App.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
  // Mock regions
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve([{ id: 1, name: 'Санкт-Петербург', code: 'spb' }])
  } as Response)
  // Mock listings
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 50 })
  } as Response)
  // Mock stats
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ total: 0, agent_count: 0, private_count: 0, new_today: 0, by_source: { avito: 0, cian: 0 } })
  } as Response)
})

describe('App', () => {
  it('renders header and filter summary', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Hata')).toBeDefined()
    })
  })

  it('renders stats widget', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('📊 Статистика')).toBeDefined()
    })
  })

  it('renders parse widget', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('⚙ Парсинг')).toBeDefined()
    })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: FAIL — current App is scaffold boilerplate

- [ ] **Step 3: Write App.tsx**

```tsx
// frontend/src/App.tsx
import { useState, useEffect, useCallback, useRef } from 'react'
import type { Listing, ListingFilters, Stats, Region, ParseStatus } from './types'
import { fetchListings, fetchListing, fetchRegions, fetchStats, startParse, fetchParseStatus } from './api'
import { FilterBar } from './components/FilterBar'
import { ListingFeed } from './components/ListingFeed'
import { ListingModal } from './components/ListingModal'
import { StatsWidget } from './components/StatsWidget'
import { ParseWidget } from './components/ParseWidget'
import './App.css'

export default function App() {
  const [regions, setRegions] = useState<Region[]>([])
  const [listings, setListings] = useState<Listing[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null)
  const [parseStatus, setParseStatus] = useState<ParseStatus | null>(null)
  const [filters, setFilters] = useState<ListingFilters>({})
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // Load regions on mount
  useEffect(() => {
    fetchRegions().then(setRegions)
  }, [])

  // Debounced filter application
  const handleFilterChange = useCallback((patch: Partial<ListingFilters>) => {
    setFilters(prev => {
      const next = { ...prev, ...patch }
      // Reset page on filter change (unless page itself changed)
      if (!('page' in patch)) next.page = 1
      return next
    })
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      loadData(filters)
    }, 300)
  }, [filters])

  // Load listings and stats
  const loadData = useCallback(async (f: ListingFilters) => {
    try {
      const [listingData, statsData] = await Promise.all([
        fetchListings({ ...f, page: f.page ?? 1, per_page: f.per_page ?? 50 }),
        fetchStats(f.region_id),
      ])
      setListings(listingData.items)
      setTotal(listingData.total)
      setPage(listingData.page)
      setStats(statsData)
    } catch (e) {
      console.error('Failed to load data:', e)
    }
  }, [])

  // Initial load
  useEffect(() => {
    if (regions.length > 0) loadData(filters)
  }, [regions]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reload on page change
  const handlePageChange = useCallback((p: number) => {
    const next = { ...filters, page: p }
    setFilters(next)
    setPage(p)
    loadData(next)
  }, [filters, loadData])

  // Listing detail
  const handleListingClick = useCallback(async (id: number) => {
    try {
      const listing = await fetchListing(id)
      setSelectedListing(listing)
    } catch (e) {
      console.error('Failed to load listing:', e)
    }
  }, [])

  // Parse control
  const handleStartParse = useCallback(async (source: string) => {
    const regionId = filters.region_id
    if (!regionId) {
      alert('Выберите регион для запуска парсинга')
      return
    }
    try {
      const result = await startParse(regionId, source)
      setParseStatus({ task_id: result.task_id, status: result.status })
      // Poll for status
      const poll = setInterval(async () => {
        const status = await fetchParseStatus(result.task_id)
        setParseStatus(status)
        if (status.status === 'SUCCESS' || status.status === 'FAILURE') {
          clearInterval(poll)
          loadData(filters) // Refresh data
        }
      }, 2000)
    } catch (e) {
      console.error('Failed to start parse:', e)
    }
  }, [filters, loadData])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Hata</h1>
      </header>

      <main className="app-main">
        <div className="app-left">
          <FilterBar regions={regions} filters={filters} onChange={handleFilterChange} />
          <ListingFeed
            listings={listings}
            total={total}
            page={page}
            perPage={50}
            onPageChange={handlePageChange}
            onListingClick={handleListingClick}
          />
        </div>

        <aside className="app-right">
          <StatsWidget stats={stats} />
          <ParseWidget onStartParse={handleStartParse} lastStatus={parseStatus} />
        </aside>
      </main>

      {selectedListing && (
        <ListingModal listing={selectedListing} onClose={() => setSelectedListing(null)} />
      )}
    </div>
  )
}
```

- [ ] **Step 4: Write index.css (theme + base)**

```css
/* frontend/src/index.css */
:root {
  --bg: #ffffff;
  --bg-secondary: #f5f5f5;
  --text: #1a1a1a;
  --text-muted: #888888;
  --border: #e0e0e0;
  --accent: #1976d2;
  --private: #2e7d32;
  --private-bg: #e8f5e9;
  --agent: #c62828;
  --agent-bg: #ffebee;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text);
  background: var(--bg);
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --bg-secondary: #2a2a2a;
    --text: #e0e0e0;
    --text-muted: #888888;
    --border: #333333;
    --accent: #64b5f6;
    --private: #66bb6a;
    --private-bg: #1b3a1b;
    --agent: #ef5350;
    --agent-bg: #3a1b1b;
    --shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  }
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  min-height: 100vh;
}

button {
  cursor: pointer;
}

input, select {
  font: inherit;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
}
```

- [ ] **Step 5: Write App.css (layout + component styles)**

```css
/* frontend/src/App.css */
.app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px 16px;
}

.app-header {
  padding: 8px 0 16px;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 700;
}

.app-main {
  display: flex;
  gap: 20px;
}

.app-left {
  flex: 1;
  min-width: 0;
}

.app-right {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* FilterBar */
.filter-bar {
  margin-bottom: 12px;
}

.filter-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text);
  font: inherit;
  font-size: 13px;
}

.filter-chevron {
  font-size: 10px;
  color: var(--text-muted);
}

.filter-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 6px 6px;
  background: var(--bg-secondary);
}

.filter-panel label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: var(--text-muted);
}

.filter-panel input,
.filter-panel select {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
}

.filter-panel input[type="number"] {
  width: 90px;
}

.filter-panel input[type="text"] {
  width: 140px;
}

.checkbox-label {
  flex-direction: row !important;
  align-items: center;
  gap: 6px !important;
  font-size: 13px !important;
}

/* ListingFeed */
.listing-feed {
  display: flex;
  flex-direction: column;
}

.listing-rows {
  display: flex;
  flex-direction: column;
}

.listing-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.1s;
}

.listing-row:hover {
  background: var(--bg-secondary);
}

.listing-rooms {
  font-weight: 600;
  min-width: 90px;
}

.listing-price {
  color: var(--agent);
  font-weight: 600;
  min-width: 120px;
}

.listing-location {
  color: var(--text-muted);
  min-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.listing-badge {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.listing-badge.private {
  background: var(--private-bg);
  color: var(--private);
}

.listing-badge.agent {
  background: var(--agent-bg);
  color: var(--agent);
}

.listing-time {
  font-size: 10px;
  color: var(--text-muted);
  min-width: 50px;
  text-align: right;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-muted);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 16px 0;
}

.pagination button {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
}

.pagination button.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: default;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background: var(--bg);
  border-radius: 8px;
  max-width: 560px;
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  font-size: 16px;
  font-weight: 600;
}

.modal-close {
  border: none;
  background: none;
  font-size: 18px;
  color: var(--text-muted);
  padding: 4px;
}

.modal-body {
  padding: 16px 20px;
}

.modal-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--agent);
  margin-bottom: 16px;
}

.modal-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-description {
  margin-bottom: 16px;
}

.modal-description p {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
}

.modal-link {
  color: var(--accent);
  font-size: 13px;
  text-decoration: none;
}

.modal-link:hover {
  text-decoration: underline;
}

.text-agent {
  color: var(--agent);
}

.text-private {
  color: var(--private);
}

/* Widgets */
.widget {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-secondary);
}

.widget h3 {
  font-size: 13px;
  margin-bottom: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 12px;
}

.stat-divider {
  border-top: 1px solid var(--border);
  margin: 6px 0;
}

.parse-btn {
  display: block;
  width: 100%;
  margin-bottom: 6px;
  padding: 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: 12px;
}

.parse-btn:hover {
  background: var(--accent);
  color: white;
}

.parse-status {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
}
```

- [ ] **Step 6: Update main.tsx to remove StrictMode (double-render issue with debounce)**

Not needed — StrictMode is fine for production. No changes.

- [ ] **Step 7: Run integration test**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 8: Run all tests**

Run: `cd frontend && npx vitest run`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/index.css frontend/src/App.css
git commit -m "feat: integrate all components into App with styles"
```
