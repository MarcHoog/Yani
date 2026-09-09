import { useEffect, useState, type FormEvent } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import { Button, Checklist, Markdown, MarkdownInput, SidePanel } from '@yani/ui'
import type { components } from '../api/schema'
import { emptyDetail, newId, readCardDetail, writeCardDetail, type CardDetail } from './cardBody'

type CardRead = components['schemas']['CardRead']
type CardUpdate = components['schemas']['CardUpdate']

export type CardPanelProps = {
  card: CardRead | undefined
  open: boolean
  onClose: () => void
  onSave: (cardId: string, patch: CardUpdate) => Promise<void>
}

const when = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function CardPanel({ card, open, onClose, onSave }: CardPanelProps) {
  const [title, setTitle] = useState('')
  const [editingDescription, setEditingDescription] = useState(false)
  const [description, setDescription] = useState('')
  const [comment, setComment] = useState('')
  const detail = card ? readCardDetail(card.body) : emptyDetail

  useEffect(() => {
    setTitle(card?.title ?? '')
    setEditingDescription(false)
    setComment('')
  }, [card?.id, card?.title])

  function saveDetail(next: CardDetail) {
    if (!card) return
    void onSave(card.id, { body: writeCardDetail(card.body, next) })
  }

  function commitTitle() {
    if (!card) return
    const next = title.trim()
    if (!next || next === card.title) {
      setTitle(card.title)
      return
    }
    void onSave(card.id, { title: next })
  }

  function editDescription() {
    setDescription(detail.description)
    setEditingDescription(true)
  }

  function commitDescription() {
    setEditingDescription(false)
    if (description !== detail.description) saveDetail({ ...detail, description })
  }

  function addComment(event: FormEvent) {
    event.preventDefault()
    if (!comment.trim()) return
    saveDetail({
      ...detail,
      comments: [...detail.comments, { id: newId(), text: comment.trim(), at: new Date().toISOString() }],
    })
    setComment('')
  }

  return (
    <SidePanel
      open={open}
      label={card?.title ?? 'Card'}
      onClose={onClose}
      title={
        <input
          className="card-panel-title"
          value={title}
          aria-label="Card title"
          onChange={(event) => setTitle(event.target.value)}
          onBlur={commitTitle}
          onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
        />
      }
    >
      <section className="card-panel-section">
        <div className="card-panel-section-head">
          <h3 className="card-panel-label">Description</h3>
          {!editingDescription && (
            <Button variant="ghost" size="sm" icon={<Pencil />} aria-label="Edit description" onClick={editDescription} />
          )}
        </div>
        {editingDescription ? (
          <>
            <MarkdownInput value={description} onChange={setDescription} placeholder="Markdown welcome" autoFocus />
            <div className="card-panel-row">
              <Button variant="primary" size="sm" onClick={commitDescription}>
                Save
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setEditingDescription(false)}>
                Cancel
              </Button>
            </div>
          </>
        ) : (
          <Markdown empty="No description yet">{detail.description}</Markdown>
        )}
      </section>

      <section className="card-panel-section">
        <h3 className="card-panel-label">Todo</h3>
        <Checklist
          items={detail.todos}
          placeholder="Add a step"
          onToggle={(id) =>
            saveDetail({
              ...detail,
              todos: detail.todos.map((todo) => (todo.id === id ? { ...todo, done: !todo.done } : todo)),
            })
          }
          onAdd={(text) => saveDetail({ ...detail, todos: [...detail.todos, { id: newId(), text, done: false }] })}
          onRemove={(id) => saveDetail({ ...detail, todos: detail.todos.filter((todo) => todo.id !== id) })}
        />
      </section>

      <section className="card-panel-section">
        <h3 className="card-panel-label">Comments</h3>
        {detail.comments.length === 0 && <p className="card-panel-none">No comments yet</p>}
        {detail.comments.map((entry) => (
          <article key={entry.id} className="card-panel-comment">
            <header className="card-panel-comment-head">
              <span className="card-panel-comment-when">{when.format(new Date(entry.at))}</span>
              <Button
                variant="ghost"
                size="sm"
                icon={<Trash2 />}
                aria-label="Delete comment"
                onClick={() =>
                  saveDetail({ ...detail, comments: detail.comments.filter((c) => c.id !== entry.id) })
                }
              />
            </header>
            <Markdown>{entry.text}</Markdown>
          </article>
        ))}
        <form className="card-panel-composer" onSubmit={addComment}>
          <MarkdownInput value={comment} onChange={setComment} placeholder="Write a comment" rows={3} />
          <div className="card-panel-row">
            <Button variant="primary" size="sm" type="submit" disabled={!comment.trim()}>
              Comment
            </Button>
          </div>
        </form>
      </section>
    </SidePanel>
  )
}
