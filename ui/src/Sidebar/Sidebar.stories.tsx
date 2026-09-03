import { CustomerSwitcher } from '../CustomerSwitcher/CustomerSwitcher'
import { Sidebar, type SidebarGroup } from './Sidebar'

export default { title: 'Sidebar' }

const frame = { height: 720, display: 'flex', background: 'var(--bg)' }
const noop = () => {}

const customers = [
  { id: 'cookiecooker', name: 'CookieCooker' },
  { id: 'brouwerij-de-kroon', name: 'Brouwerij De Kroon' },
  { id: 'vanderveen-advocaten', name: 'Vanderveen Advocaten' },
]

const ssot: SidebarGroup[] = [
  { items: [{ label: 'Overview', href: '/', active: true }] },
  { title: 'Organization', items: [{ label: 'Profile', href: '/profile' }, { label: 'Sites', href: '/sites' }] },
  { title: 'Identity', items: [{ label: 'Users', href: '/users' }, { label: 'Groups', href: '/groups' }] },
  { title: 'Assets', items: [{ label: 'Devices', href: '/devices' }, { label: 'Licenses', href: '/licenses' }] },
  { title: 'Tools', items: [{ label: 'Graph explorer', href: '/graph' }, { label: 'Cypher console', href: '/cypher' }] },
]

const tickets: SidebarGroup[] = [
  { title: 'Helpdesk', items: [{ label: 'Board', href: '/board', active: true }, { label: 'Automations', href: '/automations', badge: 2 }] },
  { title: 'Links', items: [{ label: 'SSOT admin portal', href: '/ssot' }, { label: 'Customer portal', href: '/portal' }] },
]

export const Default = () => (
  <div style={frame}>
    <Sidebar brand="Yani" tag="SSOT" groups={ssot}>
      <CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={noop} />
    </Sidebar>
  </div>
)

export const WithBadge = () => (
  <div style={frame}>
    <Sidebar brand="Yani" tag="Tickets" groups={tickets}>
      <CustomerSwitcher customers={customers} currentId="brouwerij-de-kroon" onSelect={noop} />
    </Sidebar>
  </div>
)

export const Minimal = () => (
  <div style={frame}>
    <Sidebar brand="Yani" groups={[{ items: [{ label: 'Overview', href: '/' }, { label: 'Tickets', href: '/tickets' }] }]} />
  </div>
)
