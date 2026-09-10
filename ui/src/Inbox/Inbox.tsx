import { useState, type DragEvent, type FormEvent, type KeyboardEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../Button/Button'
import { Input } from '../Field/Field'
import './Inbox.css'

export type InboxItem = { id: string; title: string; description?: string }

export type InboxProps = {
  items: InboxItem[]
  title?: string
  empty?: string
  placeholder?: string
  dragType?: string
  onAdd?: (title: string) => void
  onItemClick?: (id: string) => void
  onRemove?: (id: string) => void
}

export function Inbox({
  items,
  title = 'Inbox',
  empty = 'Nothing captured',
  placeholder = 'Capture a thought',
  dragType,
  onAdd,
  onItemClick,
  onRemove,
}: InboxProps) {
  const [text, setText] = useState('')

  function add(event: FormEvent) {
    event.preventDefault()
    if (!text.trim()) return
    onAdd?.(text.trim())
    setText('')
  }

  function dragStart(event: DragEvent, id: string) {
    if (!dragType) return
    event.dataTransfer.setData(dragType, id)
    event.dataTransfer.effectAllowed = 'move'
  }

  function keyDown(event: KeyboardEvent, id: string) {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    onItemClick?.(id)
  }

  return (
    <section className="y-inbox" aria-label={title}>
      <header className="y-inbox-header">
        <h2 className="y-inbox-title">{title}</h2>
        <span className="y-inbox-count">{items.length}</span>
      </header>
      {onAdd && (
        <form className="y-inbox-add" onSubmit={add}>
          <Input value={text} placeholder={placeholder} onChange={(event) => setText(event.target.value)} />
          <Button icon={<Plus />} type="submit" aria-label="Add to inbox" disabled={!text.trim()} />
        </form>
      )}
      <div className="y-inbox-items">
        {items.length === 0 && <div className="y-inbox-none">{empty}</div>}
        {items.map((item) => (
          <article
            key={item.id}
            className="y-inbox-item"
            data-item={item.id}
            draggable={!!dragType}
            onDragStart={(event) => dragStart(event, item.id)}
          >
            <div
              className="y-inbox-item-body"
              role={onItemClick ? 'button' : undefined}
              tabIndex={onItemClick ? 0 : undefined}
              onClick={() => onItemClick?.(item.id)}
              onKeyDown={onItemClick ? (event) => keyDown(event, item.id) : undefined}
            >
              <div className="y-inbox-item-title">{item.title}</div>
              {item.description && <div className="y-inbox-item-text">{item.description}</div>}
            </div>
            {onRemove && (
              <Button
                variant="ghost"
                size="sm"
                icon={<Trash2 />}
                aria-label={`Remove ${item.title}`}
                onClick={() => onRemove(item.id)}
              />
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
