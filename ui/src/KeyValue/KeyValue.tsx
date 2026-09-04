import type { ReactNode } from 'react'
import './KeyValue.css'

export type KeyValueProps = { items: [string, ReactNode][] }

export function KeyValue({ items }: KeyValueProps) {
  return (
    <dl className="y-kv">
      {items.map(([key, value]) => (
        <div key={key} className="y-kv-item">
          <dt className="y-kv-key">{key}</dt>
          <dd className="y-kv-value">{value === null || value === undefined || value === '' ? <span className="y-kv-empty">-</span> : value}</dd>
        </div>
      ))}
    </dl>
  )
}
