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
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    fetchRegions().then(setRegions)
  }, [])

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

  useEffect(() => {
    if (regions.length > 0) loadData(filters)
  }, [regions]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleFilterChange = useCallback((patch: Partial<ListingFilters>) => {
    setFilters(prev => {
      const next = { ...prev, ...patch }
      if (!('page' in patch)) next.page = 1
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => loadData(next), 300)
      return next
    })
  }, [loadData])

  const handlePageChange = useCallback((p: number) => {
    const next = { ...filters, page: p }
    setFilters(next)
    setPage(p)
    loadData(next)
  }, [filters, loadData])

  const handleListingClick = useCallback(async (id: number) => {
    try {
      const listing = await fetchListing(id)
      setSelectedListing(listing)
    } catch (e) {
      console.error('Failed to load listing:', e)
    }
  }, [])

  const handleStartParse = useCallback(async (source: string) => {
    const regionId = filters.region_id
    if (!regionId) {
      alert('Выберите регион для запуска парсинга')
      return
    }
    try {
      const result = await startParse(regionId, source)
      setParseStatus({ task_id: result.task_id, status: result.status })
      const poll = setInterval(async () => {
        const status = await fetchParseStatus(result.task_id)
        setParseStatus(status)
        if (status.status === 'SUCCESS' || status.status === 'FAILURE') {
          clearInterval(poll)
          loadData(filters)
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
