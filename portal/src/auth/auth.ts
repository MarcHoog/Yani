import { UserManager, WebStorageStateStore, type User } from 'oidc-client-ts'

// Served next to the app: nginx renders it from env in the container, the vite dev server from
// the repo root .env. Issuer and client ID are public; nothing secret goes in here.
type AuthConfig = { issuer: string; clientId: string; projectId: string }

export const CALLBACK_PATH = '/auth/callback'
export const SIGN_OUT_PATH = '/auth/signout'

let manager: UserManager | undefined

async function loadConfig(): Promise<AuthConfig> {
  const res = await fetch('/auth-config.json', { cache: 'no-store' })
  if (!res.ok) throw new Error(`auth config unavailable (${res.status})`)
  const config = (await res.json()) as AuthConfig
  if (!config.issuer || !config.clientId || !config.projectId) {
    throw new Error('auth config incomplete: run `python dev.py seed`')
  }
  return config
}

export async function initAuth(): Promise<UserManager> {
  if (manager) return manager
  const { issuer, clientId, projectId } = await loadConfig()
  const origin = window.location.origin
  manager = new UserManager({
    authority: issuer,
    client_id: clientId,
    redirect_uri: origin + CALLBACK_PATH,
    post_logout_redirect_uri: origin + '/',
    response_type: 'code',
    // Project audience so the APIs accept the access token, project roles so it carries the role.
    scope: [
      'openid',
      'profile',
      'email',
      'offline_access',
      `urn:zitadel:iam:org:project:id:${projectId}:aud`,
      'urn:zitadel:iam:org:projects:roles',
    ].join(' '),
    userStore: new WebStorageStateStore({ store: window.sessionStorage }),
    automaticSilentRenew: true,
  })
  return manager
}

function auth(): UserManager {
  if (!manager) throw new Error('auth not initialised')
  return manager
}

/** Sends the browser to Zitadel and comes back to the current page afterwards. */
export function signIn(): Promise<void> {
  const here = window.location.pathname + window.location.search
  return auth().signinRedirect({ url_state: here })
}

export function signOut(): Promise<void> {
  return auth().signoutRedirect()
}

/** Completes the redirect back from Zitadel. Returns the page to continue on. */
export async function completeSignIn(): Promise<string> {
  const user = await auth().signinRedirectCallback()
  const target = user.url_state
  return target && target.startsWith('/') && !target.startsWith('/auth/') ? target : '/'
}

export async function currentUser(): Promise<User | null> {
  const user = await auth().getUser()
  return user && !user.expired ? user : null
}

export async function accessToken(): Promise<string | null> {
  return (await currentUser())?.access_token ?? null
}
