import type { ReactNode } from 'react'
import './StatTile.css'

export type StatTileProps = { label: string; value: ReactNode; hint?: string; icon?: ReactNode; bad?: boolean }

export function StatTile({ label, value, hint, icon, bad }: StatTileProps) {
  return (
    <div className="y-stat">
      {icon && (
        <span className="y-stat-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      <div className="y-stat-body">
        <div className="y-stat-label">{label}</div>
        <div className="y-stat-value">{value}</div>
        {hint && <div className={bad ? 'y-stat-hint y-stat-hint--bad' : 'y-stat-hint'}>{hint}</div>}
      </div>
    </div>
  )
}
