import { Inbox, MapPin, Plus } from 'lucide-react'
import { Button } from '../Button/Button'
import { EmptyState } from './EmptyState'

export default { title: 'EmptyState' }

const frame = { width: 520, padding: 16, background: 'var(--bg)' }

export const WithAction = () => (
  <div style={frame}>
    <EmptyState
      icon={<Inbox />}
      title="No tickets yet"
      text="When you ask the helpdesk for something it shows up here, with every update along the way."
      action={
        <Button variant="primary" icon={<Plus />}>
          New ticket
        </Button>
      }
    />
  </div>
)

export const TextOnly = () => (
  <div style={frame}>
    <EmptyState icon={<MapPin />} title="Select a site on the map" text="People and devices assigned to that site appear here." />
  </div>
)

export const Bare = () => (
  <div style={frame}>
    <EmptyState title="Nobody assigned here" />
  </div>
)
