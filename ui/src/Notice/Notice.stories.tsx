import { Notice } from './Notice'

export default { title: 'Notice' }

const frame = { width: 520, padding: 16, display: 'flex', flexDirection: 'column' as const, gap: 12, background: 'var(--bg)' }

export const Tones = () => (
  <div style={frame}>
    <Notice>This portal shows a read-only view of your environment. Changes go through tickets or self-service.</Notice>
    <Notice tone="success" title="Request submitted">
      Ticket #1043 was created. Follow it in Tickets.
    </Notice>
    <Notice tone="warn" title="License pool almost full">
      52 of 60 Microsoft 365 E3 seats are assigned.
    </Notice>
    <Notice tone="danger" title="Could not load tickets">
      The ticket service did not respond. Try again in a moment.
    </Notice>
  </div>
)
