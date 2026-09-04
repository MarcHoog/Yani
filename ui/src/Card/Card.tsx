import type { ReactNode } from 'react'
import './Card.css'

export type CardProps = { title?: string; actions?: ReactNode; children: ReactNode }

export function Card({ title, actions, children }: CardProps) {
  return (
    <section className="y-card">
      {(title || actions) && (
        <header className="y-card-header">
          {title && <h2 className="y-card-title">{title}</h2>}
          {actions && <div className="y-card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  )
}
