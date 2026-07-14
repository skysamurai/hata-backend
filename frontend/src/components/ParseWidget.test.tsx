import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ParseWidget } from './ParseWidget'

describe('ParseWidget', () => {
  it('renders parse buttons', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={null} />)
    expect(screen.getByRole('button', { name: /авито/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /циан/i })).toBeDefined()
  })

  it('calls onStartParse with source', async () => {
    const onStart = vi.fn()
    const user = userEvent.setup()
    render(<ParseWidget onStartParse={onStart} lastStatus={null} />)
    await user.click(screen.getByRole('button', { name: /авито/i }))
    expect(onStart).toHaveBeenCalledWith('avito')
  })

  it('shows running status when PENDING', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={{ task_id: 't1', status: 'PENDING' }} />)
    expect(screen.getByText(/выполняется/i)).toBeDefined()
  })

  it('shows done status with result', () => {
    render(<ParseWidget onStartParse={vi.fn()} lastStatus={{ task_id: 't2', status: 'SUCCESS', result: { listings_found: 42 } }} />)
    expect(screen.getByText(/42/)).toBeDefined()
    expect(screen.getByText(/42/)).toBeDefined()
  })
})
