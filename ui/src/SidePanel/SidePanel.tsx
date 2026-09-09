import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Maximize2, Minimize2, X } from 'lucide-react'
import { Button } from '../Button/Button'
import './SidePanel.css'

export type SidePanelProps = {
  open: boolean
  label: string
  onClose: () => void
  title?: ReactNode
  actions?: ReactNode
  defaultFullscreen?: boolean
  children: ReactNode
}

export function SidePanel({ open, label, onClose, title, actions, defaultFullscreen = false, children }: SidePanelProps) {
  const [fullscreen, setFullscreen] = useState(defaultFullscreen)
  const panel = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!open) return
    const closeOutside = (event: MouseEvent) => {
      if (!panel.current?.contains(event.target as Node)) onClose()
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('click', closeOutside, true)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('click', closeOutside, true)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open, onClose])

  const classes = ['y-panel-layer', open && 'y-panel-layer--open', fullscreen && 'y-panel-layer--full']

  return (
    <div className={classes.filter(Boolean).join(' ')} inert={!open}>
      <aside ref={panel} className="y-panel" role="dialog" aria-modal={fullscreen} aria-label={label}>
        <header className="y-panel-head">
          <div className="y-panel-title">{title}</div>
          {actions && <div className="y-panel-actions">{actions}</div>}
          <Button
            variant="ghost"
            size="sm"
            icon={fullscreen ? <Minimize2 /> : <Maximize2 />}
            aria-label={fullscreen ? 'Leave fullscreen' : 'Fullscreen'}
            onClick={() => setFullscreen(!fullscreen)}
          />
          <Button variant="ghost" size="sm" icon={<X />} aria-label="Close" onClick={onClose} />
        </header>
        <div className="y-panel-body">{children}</div>
      </aside>
    </div>
  )
}
