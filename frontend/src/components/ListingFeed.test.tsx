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
        listings={mockListings} total={2} page={1} perPage={50}
        onPageChange={vi.fn()} onListingClick={vi.fn()}
      />
    )
    expect(screen.getByText(/2-к, 65 м²/)).toBeDefined()
    expect(screen.getByText(/12 000 000 ₽/)).toBeDefined()
  })

  it('shows private badge', () => {
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

  it('calls onListingClick when row clicked', async () => {
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
