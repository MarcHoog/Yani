import { Pencil } from 'lucide-react'
import { Button } from '../Button/Button'
import { Card } from './Card'

export default { title: 'Card' }

const frame = { width: 420, padding: 16, background: 'var(--bg)' }

export const Default = () => (
  <div style={frame}>
    <Card title="Entra tenant">
      <p style={{ fontSize: '0.9rem' }}>cookiecooker.onmicrosoft.com, 2 verified domains, 48 licensed users.</p>
    </Card>
  </div>
)

export const WithActions = () => (
  <div style={frame}>
    <Card
      title="Contact details"
      actions={
        <Button size="sm" variant="ghost" icon={<Pencil />}>
          Edit
        </Button>
      }
    >
      <p style={{ fontSize: '0.9rem' }}>Els Vermeulen, Operations. Reachable on weekdays 8:00 to 17:00.</p>
    </Card>
  </div>
)

export const Plain = () => (
  <div style={frame}>
    <Card>
      <p style={{ fontSize: '0.9rem' }}>No header, content only.</p>
    </Card>
  </div>
)
