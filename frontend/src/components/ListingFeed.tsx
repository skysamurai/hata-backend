import type { Listing } from '../types'

interface ListingFeedProps {
  listings: Listing[]
  total: number
  page: number
  perPage: number
  onPageChange: (page: number) => void
  onListingClick: (id: number) => void
}

function priceStr(price: number | null): string {
  if (price == null) return '—'
  return price.toLocaleString('ru-RU') + ' ₽'
}

function roomsStr(r: number | null): string {
  if (r == null) return '—'
  if (r === 0) return 'Студия'
  return `${r}-к`
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} мин`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} ч`
  return `${Math.floor(hours / 24)} д`
}

export function ListingFeed({ listings, total, page, perPage, onPageChange, onListingClick }: ListingFeedProps) {
  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="listing-feed">
      {listings.length === 0 ? (
        <div className="empty-state">Нет объявлений. Измените фильтры.</div>
      ) : (
        <>
          <div className="listing-rows">
            {listings.map(l => (
              <div
                key={l.id}
                className="listing-row"
                onClick={() => onListingClick(l.id)}
                role="button"
                tabIndex={0}
                onKeyDown={e => { if (e.key === 'Enter') onListingClick(l.id) }}
              >
                <span className="listing-rooms">{roomsStr(l.rooms)}, {l.area} м²</span>
                <span className="listing-price">{priceStr(l.price)}</span>
                <span className="listing-location">📍 {l.address}{l.metro ? `, м. ${l.metro}` : ''}</span>
                <span className={`listing-badge ${l.is_agent ? 'agent' : 'private'}`}>
                  {l.is_agent ? `Агент ${l.agent_score}` : 'Частное'}
                </span>
                <span className="listing-time">{timeAgo(l.last_seen)}</span>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>←</button>
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                const p = i + 1
                return (
                  <button
                    key={p}
                    className={p === page ? 'active' : ''}
                    onClick={() => onPageChange(p)}
                  >{p}</button>
                )
              })}
              <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>→</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
