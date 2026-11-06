import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

// Dev twin of the /auth-config.json that nginx serves in the container, read from the repo root
// .env that `python dev.py seed` writes.
function authConfig(): Plugin {
  return {
    name: 'yani-auth-config',
    configureServer(server) {
      const env = loadEnv('development', '..', '')
      const body = JSON.stringify({
        issuer: env.AUTH_ISSUER || 'http://zitadel.localhost:8081',
        clientId: env.PORTAL_CLIENT_ID ?? '',
        projectId: env.AUTH_AUDIENCE ?? '',
      })
      server.middlewares.use('/auth-config.json', (_req, res) => {
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Cache-Control', 'no-store')
        res.end(body)
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), authConfig()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://localhost:8010' },
  },
})
