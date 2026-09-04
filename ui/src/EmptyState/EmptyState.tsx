import type { ReactNode } from 'react'
import './EmptyState.css'

export type EmptyStateProps = { icon?: ReactNode; title: string; text?: string; action?: ReactNode }

export function EmptyState({ icon, title, text, action }: EmptyStateProps) {
  return (
    <div className="y-empty">
      {icon && (
        <span className="y-empty-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      <div className="y-empty-title">{title}</div>
      {text && <p className="y-empty-text">{text}</p>}
      {action && <div className="y-empty-action">{action}</div>}
    </div>
  )
}
