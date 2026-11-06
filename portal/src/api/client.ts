import createClient, { type Middleware } from 'openapi-fetch'
import { accessToken, signIn } from '../auth/auth'
import type { paths } from './schema'

// Every call carries the signed-in user's access token. A 401 means the session is gone:
// back to Zitadel, then to the same page.
const bearer: Middleware = {
  async onRequest({ request }) {
    const token = await accessToken()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
  async onResponse({ response }) {
    if (response.status === 401) await signIn()
    return response
  },
}

export const api = createClient<paths>()
api.use(bearer)
