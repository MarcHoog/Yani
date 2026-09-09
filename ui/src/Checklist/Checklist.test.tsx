import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { Checklist } from './Checklist'
import * as stories from './Checklist.stories'
import { screenshotStories } from '../test/screenshots'

const items = [
  { id: 't1', text: 'Slide the panel in', done: true },
  { id: 't2', text: 'Render the markdown', done: false },
]

test('shows progress and item state', async () => {
  const screen = await render(<Checklist items={items} onToggle={() => {}} />)

  await expect.element(screen.getByText('1 of 2 done')).toBeVisible()
  expect(screen.getByRole('checkbox', { name: 'Slide the panel in' }).element()).toHaveProperty('checked', true)
})

test('empty hint when there is nothing to do', async () => {
  const screen = await render(<Checklist items={[]} onToggle={() => {}} />)

  await expect.element(screen.getByText('Nothing to do yet')).toBeVisible()
})

test('toggling an item calls onToggle', async () => {
  const onToggle = vi.fn()
  const screen = await render(<Checklist items={items} onToggle={onToggle} />)

  await screen.getByRole('checkbox', { name: 'Render the markdown' }).click()

  expect(onToggle).toHaveBeenCalledWith('t2')
})

test('submitting the add row calls onAdd and clears it', async () => {
  const onAdd = vi.fn()
  const screen = await render(<Checklist items={items} onToggle={() => {}} onAdd={onAdd} />)

  await screen.getByPlaceholder('Add an item').fill('Wire the comments')
  await screen.getByRole('button', { name: 'Add item' }).click()

  expect(onAdd).toHaveBeenCalledWith('Wire the comments')
  expect(screen.getByPlaceholder('Add an item').element()).toHaveProperty('value', '')
})

test('remove button calls onRemove', async () => {
  const onRemove = vi.fn()
  const screen = await render(<Checklist items={items} onToggle={() => {}} onRemove={onRemove} />)

  await screen.getByRole('button', { name: 'Remove Render the markdown' }).click()

  expect(onRemove).toHaveBeenCalledWith('t2')
})

screenshotStories(stories)
