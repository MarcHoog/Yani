import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { components } from '../api/schema'

export type BoardData = components['schemas']['Board']

export function useBoard() {
  const [board, setBoard] = useState<BoardData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    const { data } = await api.GET('/api/v1/board')
    if (!data) {
      setError('Could not load the board. Is todo-api running?')
      return
    }
    setBoard(data)
    setError(null)
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  const addCard = useCallback(
    async (columnId: string, title: string) => {
      const { data } = await api.POST('/api/v1/cards', { body: { column_id: columnId, title } })
      if (!data) setError('Could not create the card')
      await reload()
    },
    [reload],
  )

  const moveCard = useCallback(
    async (cardId: string, toColumnId: string) => {
      setBoard((current) => {
        if (!current) return current
        const card = current.columns.flatMap((column) => column.cards).find((c) => c.id === cardId)
        if (!card || card.column_id === toColumnId) return current
        return {
          columns: current.columns.map((column) => ({
            ...column,
            cards:
              column.id === toColumnId
                ? [...column.cards, { ...card, column_id: toColumnId }]
                : column.cards.filter((c) => c.id !== cardId),
          })),
        }
      })
      const { data } = await api.PATCH('/api/v1/cards/{card_id}', {
        params: { path: { card_id: cardId } },
        body: { column_id: toColumnId },
      })
      if (!data) setError('Could not move the card')
      await reload()
    },
    [reload],
  )

  return { board, error, reload, addCard, moveCard }
}
