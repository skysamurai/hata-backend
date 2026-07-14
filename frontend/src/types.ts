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
