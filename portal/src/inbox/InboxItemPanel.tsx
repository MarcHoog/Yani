import { useEffect, useState } from 'react'
import { Pencil } from 'lucide-react'
import { Button, Markdown, MarkdownInput, SidePanel } from '@yani/ui'
import { readDescription, writeDescription } from './inboxItem'
import type { InboxItemData, InboxItemUpdate } from './useInbox'

export type InboxItemPanelProps = {
  item: InboxItemData | undefined
  open: boolean
  onClose: () => void
  onSave: (itemId: string, patch: InboxItemUpdate) => Promise<void>
}

export function InboxItemPanel({ item, open, onClose, onSave }: InboxItemPanelProps) {
  const [title, setTitle] = useState('')
  const [editing, setEditing] = useState(false)
  const [description, setDescription] = useState('')
  const current = item ? readDescription(item.body) : ''

  useEffect(() => {
    setTitle(item?.title ?? '')
    setEditing(false)
  }, [item?.id, item?.title])

  function commitTitle() {
    if (!item) return
    const next = title.trim()
    if (!next || next === item.title) {
      setTitle(item.title)
      return
    }
    void onSave(item.id, { title: next })
  }

  function edit() {
    setDescription(current)
    setEditing(true)
  }

  function commitDescription() {
    setEditing(false)
    if (item && description !== current) void onSave(item.id, { body: writeDescription(item.body, description) })
  }

  return (
    <SidePanel
      open={open}
      label={item?.title ?? 'Inbox item'}
      onClose={onClose}
      title={
        <input
          className="card-panel-title"
          value={title}
          aria-label="Inbox item title"
          onChange={(event) => setTitle(event.target.value)}
          onBlur={commitTitle}
          onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
        />
      }
    >
      <section className="card-panel-section">
        <div className="card-panel-section-head">
          <h3 className="card-panel-label">Description</h3>
          {!editing && <Button variant="ghost" size="sm" icon={<Pencil />} aria-label="Edit description" onClick={edit} />}
        </div>
        {editing ? (
          <>
            <MarkdownInput value={description} onChange={setDescription} placeholder="Markdown welcome" autoFocus />
            <div className="card-panel-row">
              <Button variant="primary" size="sm" onClick={commitDescription}>
                Save
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            </div>
          </>
        ) : (
          <Markdown empty="No description yet">{current}</Markdown>
        )}
      </section>
      <p className="inbox-panel-hint">
        Drag this item onto a column to make it a card, or onto a card to add it as a todo and a comment.
      </p>
    </SidePanel>
  )
}
