import type { MouseEvent, ReactNode } from 'react'
import { ThemeToggle } from '../ThemeToggle/ThemeToggle'
import './Sidebar.css'

export type SidebarItem = { label: string; href: string; icon?: ReactNode; active?: boolean; badge?: string | number }
export type SidebarGroup = { title?: string; items: SidebarItem[] }

export type SidebarProps = {
  brand: string
  tag?: string
  logo?: ReactNode
  groups: SidebarGroup[]
  collapsed?: boolean
  children?: ReactNode
  onNavigate?: (href: string) => void
}

export function Sidebar({ brand, tag, logo, groups, collapsed = false, children, onNavigate }: SidebarProps) {
  function click(e: MouseEvent<HTMLAnchorElement>, href: string) {
    if (!onNavigate || !href.startsWith('/') || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return
    e.preventDefault()
    onNavigate(href)
  }

  return (
    <aside className={collapsed ? 'y-sidebar y-sidebar--collapsed' : 'y-sidebar'}>
      <div className="y-sidebar-brand">
        <span className="y-sidebar-logo" aria-hidden="true">
          {logo ?? brand.charAt(0)}
        </span>
        <span className="y-sidebar-brand-text">
          <span className="y-sidebar-brand-name">{brand}</span>
          {tag && <span className="y-sidebar-brand-tag">{tag}</span>}
        </span>
      </div>

      {!collapsed && children}

      <nav className="y-sidebar-nav">
        {groups.map((group, i) => (
          <div key={group.title ?? i} className="y-sidebar-group">
            {group.title && <div className="y-sidebar-group-title">{group.title}</div>}
            {group.items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="y-sidebar-link"
                title={collapsed ? item.label : undefined}
                aria-current={item.active ? 'page' : undefined}
                onClick={(e) => click(e, item.href)}
              >
                <span className="y-sidebar-icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="y-sidebar-label">{item.label}</span>
                {item.badge !== undefined && <span className="y-sidebar-badge">{item.badge}</span>}
              </a>
            ))}
          </div>
        ))}
      </nav>

      <div className="y-sidebar-footer">
        <ThemeToggle />
      </div>
    </aside>
  )
}
