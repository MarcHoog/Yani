import type { ReactNode } from 'react'
import './PageHeader.css'

export type PageHeaderProps = { title: string; sub?: string; actions?: ReactNode }

export function PageHeader({ title, sub, actions }: PageHeaderProps) {
  return (
    <header className="y-page-header">
      <div className="y-page-header-text">
        <h1 className="y-page-title">{title}</h1>
        {sub && <p className="y-page-sub">{sub}</p>}
      </div>
      {actions && <div className="y-page-actions">{actions}</div>}
    </header>
  )
}
