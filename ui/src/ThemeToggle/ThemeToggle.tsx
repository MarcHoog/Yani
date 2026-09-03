import { useEffect, useSyncExternalStore } from 'react'
import './ThemeToggle.css'

export type Theme = 'light' | 'dark'
export type ThemePreference = Theme | 'system'

const KEY = 'theme'
const listeners = new Set<() => void>()

function readPreference(): ThemePreference {
  const stored = localStorage.getItem(KEY)
  return stored === 'light' || stored === 'dark' ? stored : 'system'
}

function readResolved(): Theme {
  const preference = readPreference()
  if (preference !== 'system') return preference
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function notify() {
  for (const listener of listeners) listener()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  const osDark = matchMedia('(prefers-color-scheme: dark)')
  osDark.addEventListener('change', notify)
  return () => {
    listeners.delete(listener)
    osDark.removeEventListener('change', notify)
  }
}

export function setTheme(next: ThemePreference) {
  if (next === 'system') localStorage.removeItem(KEY)
  else localStorage.setItem(KEY, next)
  notify()
}

export function useTheme() {
  const preference = useSyncExternalStore(subscribe, readPreference)
  const resolved = useSyncExternalStore(subscribe, readResolved)

  useEffect(() => {
    document.documentElement.dataset.theme = resolved
  }, [resolved])

  return { preference, resolved, set: setTheme }
}

export function ThemeToggle() {
  const { resolved, set } = useTheme()
  const dark = resolved === 'dark'

  return (
    <button
      type="button"
      className="y-theme-toggle"
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={() => set(dark ? 'light' : 'dark')}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill={dark ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth={dark ? 1 : 2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M9 18h6" />
        <path d="M10 22h4" />
        <path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2Z" />
      </svg>
    </button>
  )
}
