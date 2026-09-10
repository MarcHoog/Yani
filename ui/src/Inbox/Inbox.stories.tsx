import { Inbox, type InboxItem } from './Inbox'

export default { title: 'Inbox' }

const wrap = { width: 280, padding: 16, background: 'var(--bg)' }

const items: InboxItem[] = [
  { id: 'i1', title: 'Renew the monitoring license', description: 'Vendor quote lands Friday, check the seat count first' },
  { id: 'i2', title: 'Ask Bob about the VPN split tunnel' },
  { id: 'i3', title: 'Graph sync skipped a tenant last night', description: 'Look at the Prefect run log' },
]

export const Default = () => (
  <div style={wrap}>
    <Inbox items={items} dragType="text/x-item" onAdd={() => {}} onItemClick={() => {}} onRemove={() => {}} />
  </div>
)

export const Empty = () => (
  <div style={wrap}>
    <Inbox items={[]} onAdd={() => {}} />
  </div>
)

export const ReadOnly = () => (
  <div style={wrap}>
    <Inbox items={items.slice(0, 2)} />
  </div>
)
