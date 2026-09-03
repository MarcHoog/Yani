import { Boxes, Building2, GitFork, KeyRound, LayoutDashboard, Layers, MapPin, Terminal, Ticket, Users, UsersRound, Workflow, ExternalLink } from 'lucide-react'
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
  { items: [{ label: 'Overview', href: '/', icon: <LayoutDashboard />, active: true }] },
  {
    title: 'Organization',
    items: [
      { label: 'Profile', href: '/profile', icon: <Building2 /> },
      { label: 'Sites', href: '/sites', icon: <MapPin /> },
    ],
  },
  {
    title: 'Identity',
    items: [
      { label: 'Users', href: '/users', icon: <Users /> },
      { label: 'Groups', href: '/groups', icon: <UsersRound /> },
    ],
  },
  {
    title: 'Assets',
    items: [
      { label: 'Devices', href: '/devices', icon: <Boxes /> },
      { label: 'Licenses', href: '/licenses', icon: <KeyRound /> },
    ],
  },
  {
    title: 'Tools',
    items: [
      { label: 'Graph explorer', href: '/graph', icon: <GitFork /> },
      { label: 'Cypher console', href: '/cypher', icon: <Terminal />, badge: 2 },
    ],
  },
]

const tickets: SidebarGroup[] = [
  {
    title: 'Helpdesk',
    items: [
      { label: 'Board', href: '/board', icon: <Ticket />, active: true },
      { label: 'Automations', href: '/automations', icon: <Workflow />, badge: 2 },
    ],
  },
  {
    title: 'Links',
    items: [
      { label: 'SSOT admin portal', href: '/ssot', icon: <Layers /> },
      { label: 'Customer portal', href: '/portal', icon: <ExternalLink /> },
    ],
  },
]

export const Default = () => (
  <div style={frame}>
    <Sidebar brand="Yani" tag="SSOT" groups={ssot}>
      <CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={noop} />
    </Sidebar>
  </div>
)

export const Collapsed = () => (
  <div style={frame}>
    <Sidebar brand="Yani" tag="SSOT" groups={ssot} collapsed>
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
