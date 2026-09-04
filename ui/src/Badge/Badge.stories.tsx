import { Badge } from './Badge'

export default { title: 'Badge' }

const row = { display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' as const, padding: 16 }

export const Tones = () => (
  <div style={row}>
    <Badge>Entra group</Badge>
    <Badge tone="accent">Premium</Badge>
    <Badge tone="success">Compliant</Badge>
    <Badge tone="warn">Waiting</Badge>
    <Badge tone="danger">Disabled</Badge>
  </div>
)

export const InText = () => (
  <div style={{ ...row, fontSize: '0.9rem' }}>
    <span>Ticket #1042</span>
    <Badge tone="warn">Waiting on customer</Badge>
    <Badge>Printing</Badge>
    <Badge tone="danger">High</Badge>
  </div>
)
