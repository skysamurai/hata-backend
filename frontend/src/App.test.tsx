import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve([{ id: 1, name: 'Санкт-Петербург', code: 'spb' }])
  } as Response)
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 50 })
  } as Response)
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ total: 0, agent_count: 0, private_count: 0, new_today: 0, by_source: { avito: 0, cian: 0 } })
  } as Response)
})

describe('App', () => {
  it('renders header', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Hata')).toBeDefined()
    })
  })

  it('renders stats and parse widgets', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('📊 Статистика')).toBeDefined()
      expect(screen.getByText('⚙ Парсинг')).toBeDefined()
    })
  })
})
