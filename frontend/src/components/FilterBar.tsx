import { useState } from 'react'
import type { Region, ListingFilters } from '../types'

interface FilterBarProps {
  regions: Region[]
  filters: ListingFilters
  onChange: (filters: Partial<ListingFilters>) => void
}

function filterSummary(regions: Region[], filters: ListingFilters): string {
  const parts: string[] = []
  if (filters.region_id) {
    const r = regions.find(reg => reg.id === filters.region_id)
    if (r) parts.push(r.name)
  }
  if (filters.rooms !== undefined) {
    parts.push(filters.rooms >= 4 ? `${filters.rooms}+к` : `${filters.rooms}к`)
  }
  if (filters.price_min || filters.price_max) {
    const min = filters.price_min ? `${(filters.price_min / 1_000_000).toFixed(0)}M` : ''
    const max = filters.price_max ? `${(filters.price_max / 1_000_000).toFixed(0)}M` : ''
    parts.push(`${min}–${max} ₽`)
  }
  if (filters.metro) parts.push(`м. ${filters.metro}`)
  if (filters.source) parts.push(filters.source === 'avito' ? 'Авито' : 'Циан')
  if (filters.is_agent === false) parts.push('Собственники')
  return parts.length > 0 ? parts.join(' · ') : 'Все объявления'
}

export function FilterBar({ regions, filters, onChange }: FilterBarProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="filter-bar">
      <button
        className="filter-summary"
        onClick={() => setExpanded(!expanded)}
        aria-label="Фильтры"
      >
        <span>{filterSummary(regions, filters)}</span>
        <span className="filter-chevron">{expanded ? '▴' : '▾'}</span>
      </button>

      {expanded && (
        <div className="filter-panel">
          <label>
            Регион
            <select
              aria-label="Регион"
              value={filters.region_id ?? ''}
              onChange={e => onChange({ region_id: e.target.value ? Number(e.target.value) : undefined })}
            >
              <option value="">Все регионы</option>
              {regions.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </label>

          <label>
            Комнат
            <select
              aria-label="Комнат"
              value={filters.rooms ?? ''}
              onChange={e => onChange({ rooms: e.target.value ? Number(e.target.value) : undefined })}
            >
              <option value="">Любая</option>
              <option value="0">Студия</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4+</option>
            </select>
          </label>

          <label>
            Цена от
            <input
              type="number"
              placeholder="0"
              value={filters.price_min ?? ''}
              onChange={e => onChange({ price_min: e.target.value ? Number(e.target.value) : undefined })}
            />
          </label>

          <label>
            Цена до
            <input
              type="number"
              placeholder="Любая"
              value={filters.price_max ?? ''}
              onChange={e => onChange({ price_max: e.target.value ? Number(e.target.value) : undefined })}
            />
          </label>

          <label>
            Метро
            <input
              type="text"
              placeholder="Название станции"
              value={filters.metro ?? ''}
              onChange={e => onChange({ metro: e.target.value || undefined })}
            />
          </label>

          <label>
            Источник
            <select
              aria-label="Источник"
              value={filters.source ?? ''}
              onChange={e => onChange({ source: e.target.value || undefined })}
            >
              <option value="">Все</option>
              <option value="avito">Авито</option>
              <option value="cian">Циан</option>
            </select>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.is_agent === false}
              onChange={e => onChange({ is_agent: e.target.checked ? false : undefined })}
            />
            Только собственники
          </label>
        </div>
      )}
    </div>
  )
}
