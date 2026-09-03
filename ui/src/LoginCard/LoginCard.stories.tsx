import { LoginCard } from './LoginCard'

export default { title: 'LoginCard' }

const page = { padding: 32, background: 'var(--bg)', display: 'flex', justifyContent: 'center' }
const noop = () => {}

export const Default = () => (
  <div style={page}>
    <LoginCard brand="Yani" subtitle="Sign in to the staff portal" forgotHref="#forgot" onSubmit={noop} />
  </div>
)

export const CustomerPortal = () => (
  <div style={page}>
    <LoginCard brand="Yani" subtitle="Sign in to your customer portal" forgotHref="#forgot" signupHref="#signup" onSubmit={noop} />
  </div>
)

export const WithError = () => (
  <div style={page}>
    <LoginCard brand="Yani" error="Wrong email or password." forgotHref="#forgot" onSubmit={noop} />
  </div>
)

export const Busy = () => (
  <div style={page}>
    <LoginCard brand="Yani" busy onSubmit={noop} />
  </div>
)
