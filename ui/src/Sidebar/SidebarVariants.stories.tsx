import { CustomerSwitcher } from '../CustomerSwitcher/CustomerSwitcher'
import { Sidebar, type SidebarGroup, type SidebarVariant } from './Sidebar'

export default { title: 'SidebarVariants' }

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
  { title: 'Tools', items: [{ label: 'Graph explorer', href: '/graph' }, { label: 'Cypher console', href: '/cypher', badge: 2 }] },
]

const variants: SidebarVariant[] = ['default', 'ink', 'rail', 'floating', 'dense', 'soft']

const Variant = ({ variant }: { variant: SidebarVariant }) => (
  <Sidebar brand="Yani" tag="SSOT" groups={ssot} variant={variant}>
    <CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={noop} />
  </Sidebar>
)

export const AllSideBySide = () => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 24, alignItems: 'flex-start' }}>
    {variants.map((variant) => (
      <div key={variant} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{variant}</span>
        <div style={{ ...frame, height: 640, border: '1px solid var(--border)' }}>
          <Variant variant={variant} />
        </div>
      </div>
    ))}
  </div>
)

export const Ink = () => (
  <div style={frame}>
    <Variant variant="ink" />
  </div>
)

export const Rail = () => (
  <div style={frame}>
    <Variant variant="rail" />
  </div>
)

export const Floating = () => (
  <div style={frame}>
    <Variant variant="floating" />
  </div>
)

export const Dense = () => (
  <div style={frame}>
    <Variant variant="dense" />
  </div>
)

export const Soft = () => (
  <div style={frame}>
    <Variant variant="soft" />
  </div>
)
