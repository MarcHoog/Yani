import { useState } from 'react'
import { Checklist, type ChecklistItem } from './Checklist'

export default { title: 'Checklist' }

const wrap = { maxWidth: 420, padding: 20, borderRadius: 16, background: 'var(--surface)' }

const seed: ChecklistItem[] = [
  { id: 't1', text: 'Panel slides in from the right', done: true },
  { id: 't2', text: 'Fullscreen centers the card', done: true },
  { id: 't3', text: 'Description renders markdown', done: false },
  { id: 't4', text: 'Comments render markdown', done: false },
]

export const Mixed = () => {
  const [items, setItems] = useState(seed)

  return (
    <div style={wrap}>
      <Checklist
        items={items}
        onToggle={(id) => setItems(items.map((item) => (item.id === id ? { ...item, done: !item.done } : item)))}
        onRemove={(id) => setItems(items.filter((item) => item.id !== id))}
        onAdd={(text) => setItems([...items, { id: String(items.length + 1), text, done: false }])}
      />
    </div>
  )
}

export const Empty = () => (
  <div style={wrap}>
    <Checklist items={[]} onToggle={() => {}} onAdd={() => {}} />
  </div>
)

export const ReadOnly = () => (
  <div style={wrap}>
    <Checklist items={seed} onToggle={() => {}} />
  </div>
)
