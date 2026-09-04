import type { ReactNode } from 'react'
import { CircleAlert, CircleCheck, Info, TriangleAlert } from 'lucide-react'
import './Notice.css'

export type NoticeTone = 'info' | 'success' | 'warn' | 'danger'

export type NoticeProps = { tone?: NoticeTone; title?: string; icon?: ReactNode; children: ReactNode }

const icons = { info: <Info />, success: <CircleCheck />, warn: <TriangleAlert />, danger: <CircleAlert /> }

export function Notice({ tone = 'info', title, icon, children }: NoticeProps) {
  return (
    <div className={`y-notice y-notice--${tone}`} role={tone === 'danger' ? 'alert' : 'status'}>
      <span className="y-notice-icon" aria-hidden="true">
        {icon ?? icons[tone]}
      </span>
      <div className="y-notice-body">
        {title && <div className="y-notice-title">{title}</div>}
        <div className="y-notice-text">{children}</div>
      </div>
    </div>
  )
}
