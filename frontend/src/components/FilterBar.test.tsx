import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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
    await user.click(screen.getByRole('button', { name: /фильтры/i }))
    const regionSelect = screen.getByRole('combobox', { name: /регион/i })
    await user.selectOptions(regionSelect, '1')
    expect(onChange).toHaveBeenCalledWith({ region_id: 1 })
  })
})
