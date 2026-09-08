import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { Board } from './Board'
import * as stories from './Board.stories'
import { screenshotStories } from '../test/screenshots'

const columns = [
  { id: 'todo', title: 'To do', cards: [{ id: 'c1', title: 'Ship the board' }] },
  { id: 'done', title: 'Done', cards: [] },
]

test('renders columns with card counts and empty hint', async () => {
  const screen = await render(<Board columns={columns} />)

  await expect.element(screen.getByRole('heading', { name: 'To do' })).toBeVisible()
  await expect.element(screen.getByText('Ship the board')).toBeVisible()
  await expect.element(screen.getByText('No cards')).toBeVisible()
})

test('clicking a card calls onCardClick', async () => {
  const onCardClick = vi.fn()
  const screen = await render(<Board columns={columns} onCardClick={onCardClick} />)

  await screen.getByRole('button', { name: 'Ship the board' }).click()

  expect(onCardClick).toHaveBeenCalledWith('c1')
})

test('dropping a card on a column calls onCardMove', async () => {
  const onCardMove = vi.fn()
  const screen = await render(<Board columns={columns} onCardMove={onCardMove} />)

  const card = screen.getByText('Ship the board').element().closest('.y-board-card')!
  const lane = screen.container.querySelector('[data-column="done"]')!
  const dataTransfer = new DataTransfer()

  card.dispatchEvent(new DragEvent('dragstart', { dataTransfer, bubbles: true }))
  lane.dispatchEvent(new DragEvent('drop', { dataTransfer, bubbles: true }))

  expect(onCardMove).toHaveBeenCalledWith('c1', 'done')
})

screenshotStories(stories)
