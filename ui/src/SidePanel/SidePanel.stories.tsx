import { useState } from 'react'
import { Button } from '../Button/Button'
import { SidePanel } from './SidePanel'

export default { title: 'SidePanel' }

const wrap = { contain: 'paint' as const, height: 520, padding: 16, background: 'var(--bg)' }

const body = (
  <>
    <p style={{ fontSize: '0.9rem' }}>Panel content scrolls. The header stays put.</p>
    <p style={{ marginTop: 10, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
      Click outside, press Escape or use the close button.
    </p>
  </>
)

export const Open = () => (
  <div style={wrap}>
    <SidePanel open label="Card" title="Wire MCP server to the board API" onClose={() => {}}>
      {body}
    </SidePanel>
  </div>
)

export const Fullscreen = () => (
  <div style={wrap}>
    <SidePanel open defaultFullscreen label="Card" title="Wire MCP server to the board API" onClose={() => {}}>
      {body}
    </SidePanel>
  </div>
)

export const WithActions = () => (
  <div style={wrap}>
    <SidePanel
      open
      label="Card"
      title="Repurpose catalog to work landscape"
      actions={<Button size="sm">Archive</Button>}
      onClose={() => {}}
    >
      {body}
    </SidePanel>
  </div>
)

export const Toggling = () => {
  const [open, setOpen] = useState(false)

  return (
    <div style={wrap}>
      <Button variant="primary" onClick={() => setOpen(true)}>
        Open the panel
      </Button>
      <SidePanel open={open} label="Card" title="Slides in from the right" onClose={() => setOpen(false)}>
        {body}
      </SidePanel>
    </div>
  )
}
