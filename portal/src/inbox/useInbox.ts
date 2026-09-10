import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { components } from '../api/schema'

export type InboxItemData = components['schemas']['InboxItemRead']
export type InboxItemUpdate = components['schemas']['InboxItemUpdate']

export function useInbox(onBoardChanged: () => Promise<void>) {
  const [items, setItems] = useState<InboxItemData[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    const { data } = await api.GET('/api/v1/inbox')
    if (!data) {
      setError('Could not load the inbox. Is todo-api running?')
      return
    }
    setItems(data)
    setError(null)
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  const dropLocally = useCallback((itemId: string) => {
    setItems((current) => current?.filter((item) => item.id !== itemId) ?? current)
  }, [])

  const addItem = useCallback(
    async (title: string) => {
      const { data } = await api.POST('/api/v1/inbox', { body: { title } })
      if (!data) setError('Could not add to the inbox')
      await reload()
    },
    [reload],
  )

  const updateItem = useCallback(
    async (itemId: string, patch: InboxItemUpdate) => {
      const { data } = await api.PATCH('/api/v1/inbox/{item_id}', {
        params: { path: { item_id: itemId } },
        body: patch,
      })
      if (!data) setError('Could not save the inbox item')
      await reload()
    },
    [reload],
  )

  const removeItem = useCallback(
    async (itemId: string) => {
      dropLocally(itemId)
      const { response } = await api.DELETE('/api/v1/inbox/{item_id}', { params: { path: { item_id: itemId } } })
      if (!response.ok) setError('Could not remove the inbox item')
      await reload()
    },
    [dropLocally, reload],
  )

  const promote = useCallback(
    async (itemId: string, columnId: string) => {
      dropLocally(itemId)
      const { data } = await api.POST('/api/v1/inbox/{item_id}/promote', {
        params: { path: { item_id: itemId } },
        body: { column_id: columnId },
      })
      if (!data) setError('Could not turn the inbox item into a card')
      await Promise.all([reload(), onBoardChanged()])
    },
    [dropLocally, reload, onBoardChanged],
  )

  const attach = useCallback(
    async (itemId: string, cardId: string) => {
      dropLocally(itemId)
      const { data } = await api.POST('/api/v1/inbox/{item_id}/attach', {
        params: { path: { item_id: itemId } },
        body: { card_id: cardId },
      })
      if (!data) setError('Could not add the inbox item to the card')
      await Promise.all([reload(), onBoardChanged()])
    },
    [dropLocally, reload, onBoardChanged],
  )

  return { items, error, reload, addItem, updateItem, removeItem, promote, attach }
}
