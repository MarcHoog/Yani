import { useState, type FormEvent } from 'react'
import { Plus } from 'lucide-react'
import { Board, Button, Card, Field, Input, Notice, PageHeader, Select } from '@yani/ui'
import { CardPanel } from './CardPanel'
import { cardMeta } from './cardMeta'
import { useBoard } from './useBoard'

export function BoardPage() {
  const { board, error, addCard, moveCard, updateCard } = useBoard()
  const [composing, setComposing] = useState(false)
  const [title, setTitle] = useState('')
  const [columnId, setColumnId] = useState('')
  const [openId, setOpenId] = useState<string | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const openCard = board?.columns.flatMap((column) => column.cards).find((card) => card.id === openId)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!board || !title.trim()) return
    await addCard(columnId || board.columns[0].id, title.trim())
    setTitle('')
    setComposing(false)
  }

  return (
    <>
      <PageHeader
        title="Board"
        sub="Cards live in Postgres via todo-api"
        actions={
          <Button
            variant="primary"
            icon={<Plus />}
            onClick={() => {
              setTitle('')
              setComposing(!composing)
            }}
          >
            New card
          </Button>
        }
      />

      {error && (
        <div className="board-error">
          <Notice tone="danger">{error}</Notice>
        </div>
      )}

      {composing && board && (
        <div className="board-composer">
          <Card title="New card">
            <form className="board-composer-form" onSubmit={submit}>
              <div className="board-composer-title">
                <Field label="Title" required>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="What needs doing?"
                    autoFocus
                  />
                </Field>
              </div>
              <Field label="Column">
                <Select value={columnId} onChange={(e) => setColumnId(e.target.value)}>
                  {board.columns.map((column) => (
                    <option key={column.id} value={column.id}>
                      {column.title}
                    </option>
                  ))}
                </Select>
              </Field>
              <Button variant="primary" type="submit" disabled={!title.trim()}>
                Add card
              </Button>
              <Button variant="ghost" onClick={() => setComposing(false)}>
                Cancel
              </Button>
            </form>
          </Card>
        </div>
      )}

      {!board && !error && <p className="board-loading">Loading the board...</p>}

      {board && (
        <Board
          columns={board.columns.map((column) => ({
            id: column.id,
            title: column.title,
            cards: column.cards.map((card) => ({ id: card.id, title: card.title, meta: cardMeta(card) })),
          }))}
          onCardClick={(cardId) => {
            setOpenId(cardId)
            setPanelOpen(true)
          }}
          onCardMove={(cardId, toColumnId) => void moveCard(cardId, toColumnId)}
        />
      )}

      <CardPanel card={openCard} open={panelOpen} onClose={() => setPanelOpen(false)} onSave={updateCard} />
    </>
  )
}
