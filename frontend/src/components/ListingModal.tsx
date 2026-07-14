import { useEffect } from 'react'
import type { Listing } from '../types'

interface ListingModalProps {
  listing: Listing
  onClose: () => void
}

function priceStr(price: number | null): string {
  if (price == null) return '—'
  return price.toLocaleString('ru-RU') + ' ₽'
}

export function ListingModal({ listing, onClose }: ListingModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="modal-overlay"
      data-testid="modal-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="modal-card">
        <div className="modal-header">
          <h2>{listing.title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">✕</button>
        </div>

        <div className="modal-body">
          <div className="modal-price">{priceStr(listing.price)}</div>

          <div className="modal-fields">
            <div className="modal-field">
              <span className="field-label">Адрес</span>
              <span>{listing.address || '—'}</span>
            </div>
            {listing.metro && (
              <div className="modal-field">
                <span className="field-label">Метро</span>
                <span>{listing.metro}</span>
              </div>
            )}
            <div className="modal-field">
              <span className="field-label">Комнат</span>
              <span>{listing.rooms != null ? (listing.rooms === 0 ? 'Студия' : listing.rooms) : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Площадь</span>
              <span>{listing.area ? `${listing.area} м²` : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Этаж</span>
              <span>{listing.floor != null && listing.total_floors != null ? `${listing.floor}/${listing.total_floors}` : '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Телефон</span>
              <span>{listing.phone_raw || listing.phone_formatted || '—'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Источник</span>
              <span>{listing.source === 'avito' ? 'Авито' : 'Циан'}</span>
            </div>
            <div className="modal-field">
              <span className="field-label">Статус</span>
              <span className={listing.is_agent ? 'text-agent' : 'text-private'}>
                {listing.is_agent ? `🤖 Агент (score: ${listing.agent_score})` : '👤 Частное лицо'}
              </span>
            </div>
          </div>

          {listing.description && (
            <div className="modal-description">
              <div className="field-label">Описание</div>
              <p>{listing.description}</p>
            </div>
          )}

          {listing.url && /^https?:\/\//.test(listing.url) ? (
            <a href={listing.url} target="_blank" rel="noopener noreferrer" className="modal-link">
              Открыть оригинал объявления →
            </a>
          ) : (
            <span className="modal-link" style={{ opacity: 0.5 }}>Ссылка недоступна</span>
          )}
        </div>
      </div>
    </div>
  )
}
