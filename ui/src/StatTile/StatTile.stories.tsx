import { Users, Laptop, KeyRound, Mail } from 'lucide-react'
import { StatTile } from './StatTile'

export default { title: 'StatTile' }

const grid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, padding: 16, background: 'var(--bg)' }

export const Overview = () => (
  <div style={grid}>
    <StatTile label="People" value={48} hint="3 disabled" icon={<Users />} />
    <StatTile label="Devices" value={61} hint="2 non-compliant" bad icon={<Laptop />} />
    <StatTile label="License seats" value="52 / 60" hint="8 free" icon={<KeyRound />} />
    <StatTile label="Mailboxes" value={54} icon={<Mail />} />
  </div>
)

export const NoIcon = () => (
  <div style={grid}>
    <StatTile label="Open tickets" value={7} hint="2 waiting on you" />
    <StatTile label="Resolved this month" value={23} />
  </div>
)
