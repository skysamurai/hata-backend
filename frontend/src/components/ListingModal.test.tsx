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
    expect(screen.getByText(/5\/12/)).toBeDefined()
  })

  it('calls onClose on × click', async () => {
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
