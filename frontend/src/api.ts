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
