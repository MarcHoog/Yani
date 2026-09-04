import { Plus, Trash2, Settings, Download } from 'lucide-react'
import { Button } from './Button'

export default { title: 'Button' }

const row = { display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' as const, padding: 16 }

export const Variants = () => (
  <div style={row}>
    <Button variant="primary">Save changes</Button>
    <Button>Cancel</Button>
    <Button variant="ghost">Learn more</Button>
    <Button variant="danger">Delete</Button>
  </div>
)

export const WithIcons = () => (
  <div style={row}>
    <Button variant="primary" icon={<Plus />}>
      New ticket
    </Button>
    <Button icon={<Download />}>Export</Button>
    <Button variant="ghost" icon={<Settings />} aria-label="Settings" />
    <Button variant="danger" icon={<Trash2 />}>
      Remove
    </Button>
  </div>
)

export const Small = () => (
  <div style={row}>
    <Button size="sm" variant="primary" icon={<Plus />}>
      Add
    </Button>
    <Button size="sm">Cancel</Button>
    <Button size="sm" variant="ghost" icon={<Settings />} aria-label="Settings" />
    <Button size="sm" variant="danger">
      Delete
    </Button>
  </div>
)

export const Disabled = () => (
  <div style={row}>
    <Button variant="primary" disabled>
      Save changes
    </Button>
    <Button disabled>Cancel</Button>
    <Button variant="ghost" disabled>
      Learn more
    </Button>
    <Button variant="danger" disabled>
      Delete
    </Button>
  </div>
)
