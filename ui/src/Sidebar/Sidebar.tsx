import type { MouseEvent, ReactNode } from 'react'
import { ThemeToggle } from '../ThemeToggle/ThemeToggle'
import './Sidebar.css'

export type SidebarItem = { label: string; href: string; active?: boolean; badge?: string | number }
export type SidebarGroup = { title?: string; items: SidebarItem[] }

export type SidebarProps = {
  brand: string
  tag?: string
  groups: SidebarGroup[]
  user?: string
  children?: ReactNode
  onNavigate?: (href: string) => void
}

export function Sidebar({ brand, tag, groups, user, children, onNavigate }: SidebarProps) {
  function click(e: MouseEvent<HTMLAnchorElement>, href: string) {
    if (!onNavigate) return
    e.preventDefault()
    onNavigate(href)
  }

  return (
    <aside className="y-sidebar">
      <div className="y-sidebar-brand">
        <span className="y-sidebar-dot" />
        <span>{brand}</span>
        {tag && <span className="y-sidebar-tag">{tag}</span>}
      </div>

      {children}

      <nav className="y-sidebar-nav">
        {groups.map((group, i) => (
          <div key={group.title ?? i} className="y-sidebar-group">
            {group.title && <div className="y-sidebar-group-title">{group.title}</div>}
            {group.items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="y-sidebar-link"
                aria-current={item.active ? 'page' : undefined}
                onClick={(e) => click(e, item.href)}
              >
                {item.label}
                {item.badge !== undefined && <span className="y-sidebar-badge">{item.badge}</span>}
              </a>
            ))}
          </div>
        ))}
      </nav>

      <div className="y-sidebar-footer">
        <ThemeToggle />
        {user && <span className="y-sidebar-user mono">{user}</span>}
      </div>
    </aside>
  )
}
