import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { Inbox } from './Inbox'
import * as stories from './Inbox.stories'
import { screenshotStories } from '../test/screenshots'

const items = [
  { id: 'i1', title: 'Renew the license', description: 'Quote due Friday' },
  { id: 'i2', title: 'Ask Bob' },
]

test('renders the items with a count and the empty hint when there are none', async () => {
  const screen = await render(<Inbox items={items} />)
  await expect.element(screen.getByRole('heading', { name: 'Inbox' })).toBeVisible()
  await expect.element(screen.getByText('2')).toBeVisible()
  await expect.element(screen.getByText('Quote due Friday')).toBeVisible()

  const empty = await render(<Inbox items={[]} />)
  await expect.element(empty.getByText('Nothing captured')).toBeVisible()
})

test('submitting the capture input calls onAdd and clears it', async () => {
  const onAdd = vi.fn()
  const screen = await render(<Inbox items={[]} onAdd={onAdd} />)

  const input = screen.getByPlaceholder('Capture a thought')
  await input.fill('  Call the vendor ')
  await screen.getByRole('button', { name: 'Add to inbox' }).click()

  expect(onAdd).toHaveBeenCalledWith('Call the vendor')
  await expect.element(input).toHaveValue('')
})

test('clicking an item calls onItemClick, the trash calls onRemove', async () => {
  const onItemClick = vi.fn()
  const onRemove = vi.fn()
  const screen = await render(<Inbox items={items} onItemClick={onItemClick} onRemove={onRemove} />)

  await screen.getByRole('button', { name: 'Ask Bob', exact: true }).click()
  await screen.getByRole('button', { name: 'Remove Ask Bob' }).click()

  expect(onItemClick).toHaveBeenCalledWith('i2')
  expect(onRemove).toHaveBeenCalledWith('i2')
})

test('dragging an item puts its id on the drag type', async () => {
  const screen = await render(<Inbox items={items} dragType="text/x-item" />)

  const item = screen.container.querySelector('[data-item="i1"]')!
  const dataTransfer = new DataTransfer()
  item.dispatchEvent(new DragEvent('dragstart', { dataTransfer, bubbles: true }))

  expect(dataTransfer.getData('text/x-item')).toBe('i1')
})

screenshotStories(stories)
