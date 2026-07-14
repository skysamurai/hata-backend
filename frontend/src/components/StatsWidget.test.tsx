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
  })

  it('renders placeholder when stats is null', () => {
    render(<StatsWidget stats={null} />)
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThan(0)
  })
})
