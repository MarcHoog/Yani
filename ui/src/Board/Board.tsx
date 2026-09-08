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

export type BoardProps = {
  columns: BoardColumn[]
  empty?: string
  onCardClick?: (cardId: string) => void
  onCardMove?: (cardId: string, toColumnId: string) => void
}

export function Board({ columns, empty = 'No cards', onCardClick, onCardMove }: BoardProps) {
  const [overColumn, setOverColumn] = useState<string | null>(null)

  function dragStart(event: DragEvent, cardId: string) {
    event.dataTransfer.setData('text/plain', cardId)
    event.dataTransfer.effectAllowed = 'move'
  }

  function dragOver(event: DragEvent, columnId: string) {
    if (!onCardMove) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    setOverColumn(columnId)
  }

  function dragLeave(event: DragEvent) {
    if (event.currentTarget.contains(event.relatedTarget as Node)) return
    setOverColumn(null)
  }

  function drop(event: DragEvent, columnId: string) {
    event.preventDefault()
    setOverColumn(null)
    const cardId = event.dataTransfer.getData('text/plain')
    if (cardId) onCardMove?.(cardId, columnId)
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
            onDragOver={(event) => dragOver(event, column.id)}
            onDragLeave={dragLeave}
            onDrop={(event) => drop(event, column.id)}
          >
            {column.cards.length === 0 && <div className="y-board-none">{empty}</div>}
            {column.cards.map((card) => (
              <article
                key={card.id}
                className="y-board-card"
                role={onCardClick ? 'button' : undefined}
                tabIndex={onCardClick ? 0 : undefined}
                draggable={!!onCardMove}
                onClick={() => onCardClick?.(card.id)}
                onKeyDown={onCardClick ? (event) => keyDown(event, card.id) : undefined}
                onDragStart={(event) => dragStart(event, card.id)}
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
