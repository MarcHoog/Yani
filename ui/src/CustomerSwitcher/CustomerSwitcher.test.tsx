import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { CustomerSwitcher } from './CustomerSwitcher'
import * as stories from './CustomerSwitcher.stories'
import { screenshotStories } from '../test/screenshots'

const customers = [
  { id: 'cookiecooker', name: 'CookieCooker' },
  { id: 'brouwerij-de-kroon', name: 'Brouwerij De Kroon' },
]

test('shows the connected customer and switches on pick', async () => {
  const onSelect = vi.fn()
  const screen = await render(<CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={onSelect} />)

  await expect.element(screen.getByRole('button', { name: /CookieCooker/ })).toHaveAttribute('aria-expanded', 'false')

  await screen.getByRole('button', { name: /CookieCooker/ }).click()
  await expect.element(screen.getByRole('option', { name: 'CookieCooker' })).toHaveAttribute('aria-selected', 'true')

  await screen.getByRole('option', { name: 'Brouwerij De Kroon' }).click()
  expect(onSelect).toHaveBeenCalledWith('brouwerij-de-kroon')
  await expect.element(screen.getByRole('listbox')).not.toBeInTheDocument()
})

test('picking the current customer only closes the list', async () => {
  const onSelect = vi.fn()
  const screen = await render(<CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={onSelect} />)

  await screen.getByRole('button', { name: /CookieCooker/ }).click()
  await screen.getByRole('option', { name: 'CookieCooker' }).click()

  expect(onSelect).not.toHaveBeenCalled()
  await expect.element(screen.getByRole('listbox')).not.toBeInTheDocument()
})

test('escape closes the list', async () => {
  const screen = await render(<CustomerSwitcher customers={customers} currentId="cookiecooker" onSelect={() => {}} />)

  await screen.getByRole('button', { name: /CookieCooker/ }).click()
  await expect.element(screen.getByRole('listbox')).toBeVisible()

  await screen.getByRole('button', { name: /CookieCooker/ }).element().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
  await expect.element(screen.getByRole('listbox')).not.toBeInTheDocument()
})

screenshotStories(stories)
