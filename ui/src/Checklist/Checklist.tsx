import { useState, type FormEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../Button/Button'
import { Input } from '../Field/Field'
import './Checklist.css'

export type ChecklistItem = { id: string; text: string; done: boolean }

export type ChecklistProps = {
  items: ChecklistItem[]
  onToggle: (id: string) => void
  onAdd?: (text: string) => void
  onRemove?: (id: string) => void
  placeholder?: string
  empty?: string
}

export function Checklist({ items, onToggle, onAdd, onRemove, placeholder = 'Add an item', empty = 'Nothing to do yet' }: ChecklistProps) {
  const [text, setText] = useState('')
  const done = items.filter((item) => item.done).length

  function add(event: FormEvent) {
    event.preventDefault()
    if (!text.trim()) return
    onAdd?.(text.trim())
    setText('')
  }

  return (
    <div className="y-check">
      {items.length > 0 && (
        <div className="y-check-progress">
          {done} of {items.length} done
        </div>
      )}
      {items.length === 0 && <div className="y-check-empty">{empty}</div>}
      {items.map((item) => (
        <div key={item.id} className={item.done ? 'y-check-row y-check-row--done' : 'y-check-row'}>
          <label className="y-check-label">
            <input type="checkbox" className="y-check-box" checked={item.done} onChange={() => onToggle(item.id)} />
            <span className="y-check-text">{item.text}</span>
          </label>
          {onRemove && (
            <Button
              variant="ghost"
              size="sm"
              icon={<Trash2 />}
              aria-label={`Remove ${item.text}`}
              onClick={() => onRemove(item.id)}
            />
          )}
        </div>
      ))}
      {onAdd && (
        <form className="y-check-add" onSubmit={add}>
          <Input value={text} placeholder={placeholder} onChange={(event) => setText(event.target.value)} />
          <Button icon={<Plus />} type="submit" aria-label="Add item" disabled={!text.trim()} />
        </form>
      )}
    </div>
  )
}
