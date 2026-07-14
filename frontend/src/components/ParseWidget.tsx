import type { ParseStatus } from '../types'

interface ParseWidgetProps {
  onStartParse: (source: string) => void
  lastStatus: ParseStatus | null
}

function statusText(status: ParseStatus | null): string {
  if (!status) return 'Готов к запуску'
  switch (status.status) {
    case 'PENDING':
    case 'STARTED':
      return '⏳ Выполняется...'
    case 'SUCCESS': {
      const count = (status.result as Record<string, unknown>)?.listings_found ?? '?'
      return `✓ Завершён (найдено: ${count})`
    }
    case 'FAILURE':
      return '✗ Ошибка'
    default:
      return `Статус: ${status.status}`
  }
}

export function ParseWidget({ onStartParse, lastStatus }: ParseWidgetProps) {
  return (
    <div className="widget parse-widget">
      <h3>⚙ Парсинг</h3>
      <button className="parse-btn" onClick={() => onStartParse('avito')}>
        ▶ Запустить Авито
      </button>
      <button className="parse-btn" onClick={() => onStartParse('cian')}>
        ▶ Запустить Циан
      </button>
      <div className="parse-status">{statusText(lastStatus)}</div>
    </div>
  )
}
