import type { Stats } from '../types'

interface StatsWidgetProps {
  stats: Stats | null
}

export function StatsWidget({ stats }: StatsWidgetProps) {
  return (
    <div className="widget stats-widget">
      <h3>📊 Статистика</h3>
      <div className="stat-row">
        <span>Всего</span>
        <b>{stats?.total ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>👤 Собственники</span>
        <b>{stats?.private_count ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>🤖 Агенты</span>
        <b>{stats?.agent_count ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>🆕 Сегодня</span>
        <b>{stats?.new_today ?? '—'}</b>
      </div>
      <div className="stat-divider" />
      <div className="stat-row">
        <span>Авито</span>
        <b>{stats?.by_source.avito ?? '—'}</b>
      </div>
      <div className="stat-row">
        <span>Циан</span>
        <b>{stats?.by_source.cian ?? '—'}</b>
      </div>
    </div>
  )
}
