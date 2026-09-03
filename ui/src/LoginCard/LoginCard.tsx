import { useId, type FormEvent } from 'react'
import './LoginCard.css'

export type LoginValues = { email: string; password: string; remember: boolean }

export type LoginCardProps = {
  brand: string
  title?: string
  subtitle?: string
  error?: string
  busy?: boolean
  forgotHref?: string
  signupHref?: string
  onSubmit: (values: LoginValues) => void
}

export function LoginCard({
  brand,
  title = 'Welcome back',
  subtitle = 'Sign in to continue',
  error,
  busy = false,
  forgotHref,
  signupHref,
  onSubmit,
}: LoginCardProps) {
  const id = useId()

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    onSubmit({
      email: String(data.get('email')),
      password: String(data.get('password')),
      remember: data.get('remember') === 'on',
    })
  }

  return (
    <div className="y-login">
      <div className="y-login-brand">
        <span className="y-login-dot" />
        {brand}
      </div>

      <h1 className="y-login-title">{title}</h1>
      <p className="y-login-subtitle">{subtitle}</p>

      <form className="y-login-form" onSubmit={submit}>
        <div className="y-field">
          <label htmlFor={`${id}-email`}>Email</label>
          <input id={`${id}-email`} name="email" type="email" required autoComplete="email" placeholder="you@company.com" />
        </div>

        <div className="y-field">
          <div className="y-field-row">
            <label htmlFor={`${id}-password`}>Password</label>
            {forgotHref && <a className="y-link" href={forgotHref}>Forgot password?</a>}
          </div>
          <input id={`${id}-password`} name="password" type="password" required autoComplete="current-password" />
        </div>

        <label className="y-check">
          <input name="remember" type="checkbox" />
          Remember me on this device
        </label>

        {error && <p className="y-login-error" role="alert">{error}</p>}

        <button className="y-btn" type="submit" disabled={busy}>
          {busy ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      {signupHref && (
        <>
          <div className="y-login-divider">or</div>
          <p className="y-login-signup">
            New here? <a className="y-link" href={signupHref}>Sign up</a>
          </p>
        </>
      )}
    </div>
  )
}
