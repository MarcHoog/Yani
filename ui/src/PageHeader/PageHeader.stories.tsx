import { Plus, Search } from 'lucide-react'
import { Button } from '../Button/Button'
import { Input } from '../Field/Field'
import { PageHeader } from './PageHeader'

export default { title: 'PageHeader' }

const frame = { width: 760, padding: 16, background: 'var(--bg)' }

export const TitleOnly = () => (
  <div style={frame}>
    <PageHeader title="Overview" sub="CookieCooker, food production, premium support" />
  </div>
)

export const WithSearch = () => (
  <div style={frame}>
    <PageHeader title="People" sub="48 accounts, 3 disabled" actions={<Input placeholder="Search people" style={{ width: 240 }} />} />
  </div>
)

export const WithActions = () => (
  <div style={frame}>
    <PageHeader
      title="Tickets"
      sub="7 open"
      actions={
        <>
          <Button icon={<Search />} variant="ghost" aria-label="Search" />
          <Button variant="primary" icon={<Plus />}>
            New ticket
          </Button>
        </>
      }
    />
  </div>
)
