import { StrictMode, useState, type ComponentType } from 'react'
import { createRoot } from 'react-dom/client'
import '../src/theme.css'
import './gallery.css'

type Mode = 'light' | 'dark' | 'both'
type StoryModule = { default: { title: string } } & Record<string, ComponentType>

const modules = import.meta.glob<StoryModule>('../src/**/*.stories.tsx', { eager: true })
const stories = Object.values(modules).flatMap(({ default: meta, ...variants }) =>
  Object.entries(variants).map(([name, Story]) => ({ id: `${meta.title}/${name}`, title: meta.title, name, Story })),
)
const titles = [...new Set(stories.map((s) => s.title))]

function App() {
  const [id, setId] = useState(location.hash.slice(1))
  const [mode, setMode] = useState<Mode>('both')
  const current = stories.find((s) => s.id === id) ?? stories[0]
  const themes = mode === 'both' ? (['light', 'dark'] as const) : [mode]

  function open(next: string) {
    location.hash = next
    setId(next)
  }

  return (
    <div className="g-shell">
      <nav className="g-nav">
        <div className="g-brand">@yani/ui</div>
        {titles.map((title) => (
          <div key={title} className="g-group">
            <div className="g-group-title">{title}</div>
            {stories
              .filter((s) => s.title === title)
              .map((s) => (
                <button key={s.id} className="g-link" aria-current={s.id === current.id || undefined} onClick={() => open(s.id)}>
                  {s.name}
                </button>
              ))}
          </div>
        ))}
      </nav>

      <main className="g-main">
        <header className="g-bar">
          <span className="mono">{current.id}</span>
          <div className="g-modes">
            {(['light', 'dark', 'both'] as const).map((m) => (
              <button key={m} className="g-mode" aria-pressed={m === mode} onClick={() => setMode(m)}>
                {m}
              </button>
            ))}
          </div>
        </header>
        <div className="g-panes">
          {themes.map((theme) => (
            <section key={theme} className="g-pane" data-theme={theme}>
              <current.Story />
            </section>
          ))}
        </div>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
