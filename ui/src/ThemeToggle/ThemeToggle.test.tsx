import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { ThemeToggle } from './ThemeToggle'
import * as stories from './ThemeToggle.stories'
import { screenshotStories } from '../test/screenshots'

test('toggles the document theme', async () => {
  document.documentElement.dataset.theme = 'light'
  const screen = await render(<ThemeToggle />)

  await screen.getByRole('button', { name: 'Switch to dark mode' }).click()
  expect(document.documentElement.dataset.theme).toBe('dark')

  await screen.getByRole('button', { name: 'Switch to light mode' }).click()
  expect(document.documentElement.dataset.theme).toBe('light')
})

screenshotStories(stories)
