import { CustomerSwitcher, type Customer } from './CustomerSwitcher'

export default { title: 'CustomerSwitcher' }

const frame = { width: 216, padding: 16, background: 'var(--surface)' }
const noop = () => {}

const customers: Customer[] = [
  { id: 'cookiecooker', name: 'CookieCooker' },
  { id: 'brouwerij-de-kroon', name: 'Brouwerij De Kroon' },
  { id: 'vanderveen-advocaten', name: 'Vanderveen Advocaten' },
]

export const Default = () => (
  <div style={frame}>
    <CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={noop} />
  </div>
)

export const NothingSelected = () => (
  <div style={frame}>
    <CustomerSwitcher customers={customers} currentId="" onSelect={noop} />
  </div>
)
