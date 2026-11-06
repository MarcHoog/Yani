import { useEffect, useState, type ReactNode } from 'react'
import { Notice } from '@yani/ui'
import { CALLBACK_PATH, completeSignIn, currentUser, initAuth, signIn } from './auth'

type State = { kind: 'loading' } | { kind: 'ready' } | { kind: 'error'; message: string }

/** Renders children only for a signed-in user. Everyone else is sent to Zitadel. */
export function AuthGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false
    async function start() {
      await initAuth()
      if (window.location.pathname === CALLBACK_PATH) {
        const target = await completeSignIn()
        window.history.replaceState(null, '', target)
      }
      if (await currentUser()) {
        if (!cancelled) setState({ kind: 'ready' })
        return
      }
      await signIn()
    }
    start().catch((err: unknown) => {
      if (!cancelled) setState({ kind: 'error', message: err instanceof Error ? err.message : String(err) })
    })
    return () => {
      cancelled = true
    }
  }, [])

  if (state.kind === 'error') {
    return (
      <div className="auth-screen">
        <Notice tone="danger" title="Sign-in failed">
          {state.message}
        </Notice>
      </div>
    )
  }
  if (state.kind === 'loading') return null
  return children
}
