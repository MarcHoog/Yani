import { useEffect, useRef, useState } from 'react'
import './CustomerSwitcher.css'

export type Customer = { id: string; name: string }

export type CustomerSwitcherProps = {
  customers: Customer[]
  currentId: string
  onSelect: (id: string) => void
}

function Tile({ name }: { name?: string }) {
  return (
    <span className="y-customer-tile" aria-hidden="true">
      {name ? name.charAt(0).toUpperCase() : '?'}
    </span>
  )
}

export function CustomerSwitcher({ customers, currentId, onSelect }: CustomerSwitcherProps) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const current = customers.find((c) => c.id === currentId)

  useEffect(() => {
    if (!open) return
    const closeOutside = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', closeOutside)
    return () => document.removeEventListener('pointerdown', closeOutside)
  }, [open])

  function select(id: string) {
    setOpen(false)
    if (id !== currentId) onSelect(id)
  }

  return (
    <div ref={root} className="y-customer" onKeyDown={(e) => e.key === 'Escape' && setOpen(false)}>
      <button
        type="button"
        className="y-customer-current"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <Tile name={current?.name} />
        <span className="y-customer-text">
          <span className="y-customer-name">{current?.name ?? 'Select a customer'}</span>
          <span className="y-customer-label">Customer</span>
        </span>
        <svg className="y-customer-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="y-customer-list" role="listbox" aria-label="Customers">
          {customers.map((c) => (
            <button
              key={c.id}
              type="button"
              role="option"
              aria-selected={c.id === currentId}
              className="y-customer-option"
              onClick={() => select(c.id)}
            >
              <Tile name={c.name} />
              {c.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
