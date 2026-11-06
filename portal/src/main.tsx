import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@yani/ui/theme.css'
import './app.css'
import { App } from './App'
import { AuthGate } from './auth/AuthGate'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthGate>
      <App />
    </AuthGate>
  </StrictMode>,
)
