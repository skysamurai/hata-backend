import { describe, it, expect, vi, beforeEach } from 'vitest'

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
