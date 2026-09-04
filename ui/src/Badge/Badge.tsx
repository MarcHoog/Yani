import type { ReactNode } from 'react'
import './Badge.css'

export type BadgeTone = 'neutral' | 'accent' | 'success' | 'warn' | 'danger'

export type BadgeProps = { tone?: BadgeTone; children: ReactNode }

export function Badge({ tone = 'neutral', children }: BadgeProps) {
  return <span className={`y-badge y-badge--${tone}`}>{children}</span>
}
