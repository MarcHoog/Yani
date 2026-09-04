import { Card } from '../Card/Card'
import { Meter } from './Meter'

export default { title: 'Meter' }

const frame = { width: 420, padding: 16, background: 'var(--bg)' }
const line = { display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }

export const Licenses = () => (
  <div style={frame}>
    <Card title="Microsoft 365 E3">
      <div style={line}>
        <span>Seats assigned</span>
        <span style={{ color: 'var(--text-h)', fontWeight: 600 }}>34 / 60</span>
      </div>
      <Meter value={34} max={60} label="Seats assigned" />
      <div style={{ ...line, marginTop: 18 }}>
        <span>Microsoft 365 F3</span>
        <span style={{ color: 'var(--text-h)', fontWeight: 600 }}>58 / 60</span>
      </div>
      <Meter value={58} max={60} label="Microsoft 365 F3 seats" />
    </Card>
  </div>
)
