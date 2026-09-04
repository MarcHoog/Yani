import { Badge } from '../Badge/Badge'
import { Table } from './Table'

export default { title: 'Table' }

const frame = { padding: 16, background: 'var(--bg)' }

const columns = ['Name', 'Sign-in', 'Title', 'Site', 'Licenses', 'Status']

export const People = () => (
  <div style={frame}>
    <Table
      columns={columns}
      rows={[
        ['Els Vermeulen', 'els.vermeulen@cookiecooker.be', 'Operations lead', 'Gent', <Badge>M365 E3</Badge>, <Badge tone="success">Active</Badge>],
        ['Jonas De Smet', 'jonas.desmet@cookiecooker.be', 'Baker', 'Gent', <Badge>M365 F3</Badge>, <Badge tone="success">Active</Badge>],
        ['Fatima El Amrani', 'fatima.elamrani@cookiecooker.be', null, 'Antwerpen', null, <Badge tone="danger">Disabled</Badge>],
      ]}
    />
  </div>
)

export const Empty = () => (
  <div style={frame}>
    <Table columns={columns} rows={[]} empty="No people match your search" />
  </div>
)
