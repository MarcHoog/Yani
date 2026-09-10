import { useState, type DragEvent, type KeyboardEvent, type ReactNode } from 'react'
import { Badge, type BadgeTone } from '../Badge/Badge'
import './Board.css'

export type BoardCard = {
  id: string
  title: string
  badges?: { label: string; tone?: BadgeTone }[]
  meta?: ReactNode
}

export type BoardColumn = { id: string; title: string; cards: BoardCard[] }

export type BoardDropTarget = { columnId: string; cardId?: string }

export type BoardProps = {
  columns: BoardColumn[]
  empty?: string
  onCardClick?: (cardId: string) => void
  onCardMove?: (cardId: string, toColumnId: string) => void
  accept?: string
  onDrop?: (payload: string, target: BoardDropTarget) => void
}

const CARD_TYPE = 'application/x-yani-card'

export function Board({ columns, empty = 'No cards', onCardClick, onCardMove, accept, onDrop }: BoardProps) {
  const [overColumn, setOverColumn] = useState<string | null>(null)
  const [overCard, setOverCard] = useState<string | null>(null)

  function carriesCard(event: DragEvent) {
    return !!onCardMove && event.dataTransfer.types.includes(CARD_TYPE)
  }

  function carriesForeign(event: DragEvent) {
    return !!onDrop && !!accept && event.dataTransfer.types.includes(accept)
  }

  function dragStart(event: DragEvent, cardId: string) {
    event.dataTransfer.setData(CARD_TYPE, cardId)
    event.dataTransfer.effectAllowed = 'move'
  }

  function dragOverColumn(event: DragEvent, columnId: string) {
    if (!carriesCard(event) && !carriesForeign(event)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    setOverColumn(columnId)
  }

  function dragOverCard(event: DragEvent, cardId: string) {
    if (!carriesForeign(event)) return
    event.preventDefault()
    event.stopPropagation()
    event.dataTransfer.dropEffect = 'move'
    setOverCard(cardId)
  }

  function dragLeave(event: DragEvent, clear: () => void) {
    if (event.currentTarget.contains(event.relatedTarget as Node)) return
    clear()
  }

  function dropOnColumn(event: DragEvent, columnId: string) {
    event.preventDefault()
    setOverColumn(null)
    setOverCard(null)
    const cardId = event.dataTransfer.getData(CARD_TYPE)
    if (cardId) {
      onCardMove?.(cardId, columnId)
      return
    }
    const payload = accept ? event.dataTransfer.getData(accept) : ''
    if (payload) onDrop?.(payload, { columnId })
  }

  function dropOnCard(event: DragEvent, columnId: string, cardId: string) {
    const payload = accept ? event.dataTransfer.getData(accept) : ''
    if (!payload) return
    event.preventDefault()
    event.stopPropagation()
    setOverColumn(null)
    setOverCard(null)
    onDrop?.(payload, { columnId, cardId })
  }

  function keyDown(event: KeyboardEvent, cardId: string) {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    onCardClick?.(cardId)
  }

  return (
    <div className="y-board">
      {columns.map((column) => (
        <section key={column.id} className="y-board-column" aria-label={column.title}>
          <header className="y-board-column-header">
            <h2 className="y-board-column-title">{column.title}</h2>
            <span className="y-board-column-count">{column.cards.length}</span>
          </header>
          <div
            className={`y-board-cards${overColumn === column.id ? ' y-board-cards--over' : ''}`}
            data-column={column.id}
            onDragEnter={(event) => dragOverColumn(event, column.id)}
            onDragOver={(event) => dragOverColumn(event, column.id)}
            onDragLeave={(event) => dragLeave(event, () => setOverColumn(null))}
            onDrop={(event) => dropOnColumn(event, column.id)}
          >
            {column.cards.length === 0 && <div className="y-board-none">{empty}</div>}
            {column.cards.map((card) => (
              <article
                key={card.id}
                className={`y-board-card${overCard === card.id ? ' y-board-card--over' : ''}`}
                data-card={card.id}
                role={onCardClick ? 'button' : undefined}
                tabIndex={onCardClick ? 0 : undefined}
                draggable={!!onCardMove}
                onClick={() => onCardClick?.(card.id)}
                onKeyDown={onCardClick ? (event) => keyDown(event, card.id) : undefined}
                onDragStart={(event) => dragStart(event, card.id)}
                onDragEnter={(event) => dragOverCard(event, card.id)}
                onDragOver={(event) => dragOverCard(event, card.id)}
                onDragLeave={(event) => dragLeave(event, () => setOverCard(null))}
                onDrop={(event) => dropOnCard(event, column.id, card.id)}
              >
                <div className="y-board-card-title">{card.title}</div>
                {card.badges && card.badges.length > 0 && (
                  <div className="y-board-card-badges">
                    {card.badges.map((badge) => (
                      <Badge key={badge.label} tone={badge.tone}>
                        {badge.label}
                      </Badge>
                    ))}
                  </div>
                )}
                {card.meta && <div className="y-board-card-meta">{card.meta}</div>}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
