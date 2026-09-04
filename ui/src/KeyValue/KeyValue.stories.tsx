import { Badge } from '../Badge/Badge'
import { Card } from '../Card/Card'
import { KeyValue } from './KeyValue'

export default { title: 'KeyValue' }

const frame = { width: 560, padding: 16, background: 'var(--bg)' }

export const Tenant = () => (
  <div style={frame}>
    <Card title="Entra tenant">
      <KeyValue
        items={[
          ['Tenant', 'cookiecooker.onmicrosoft.com'],
          ['Tenant id', '3f2a9c1e-7b44-4d1a-9f0e-2c8b5d6e7a90'],
          ['Primary domain', 'cookiecooker.be'],
          ['Support tier', <Badge tone="accent">Premium</Badge>],
          ['Region', 'West Europe'],
          ['Break-glass account', null],
        ]}
      />
    </Card>
  </div>
)
