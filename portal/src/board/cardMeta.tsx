import type { ReactNode } from 'react'
import { ListChecks, MessageSquare } from 'lucide-react'
import type { components } from '../api/schema'
import { readCardDetail } from './cardBody'

type CardRead = components['schemas']['CardRead']

export function cardMeta(card: CardRead): ReactNode | undefined {
  const { todos, comments } = readCardDetail(card.body)
  if (todos.length === 0 && comments.length === 0) return undefined

  return (
    <>
      {todos.length > 0 && (
        <span className="board-card-meta-item" title="Todo">
          <ListChecks />
          {todos.filter((todo) => todo.done).length}/{todos.length}
        </span>
      )}
      {comments.length > 0 && (
        <span className="board-card-meta-item" title="Comments">
          <MessageSquare />
          {comments.length}
        </span>
      )}
    </>
  )
}
