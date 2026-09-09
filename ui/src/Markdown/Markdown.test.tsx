import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Markdown } from './Markdown'
import * as stories from './Markdown.stories'
import { screenshotStories } from '../test/screenshots'

test('renders headings, emphasis and lists', async () => {
  const screen = await render(<Markdown>{'# Title\n\nSome **bold** text\n\n- one\n- two'}</Markdown>)

  await expect.element(screen.getByRole('heading', { name: 'Title' })).toBeVisible()
  await expect.element(screen.getByText('bold')).toBeVisible()
  await expect.element(screen.getByText('two')).toBeVisible()
})

test('renders gfm tables', async () => {
  const screen = await render(<Markdown>{'| a | b |\n|---|---|\n| 1 | 2 |'}</Markdown>)

  await expect.element(screen.getByRole('table')).toBeVisible()
  expect(screen.container.querySelectorAll('th')).toHaveLength(2)
  await expect.element(screen.getByText('1')).toBeVisible()
})

test('renders gfm task lists', async () => {
  const screen = await render(<Markdown>{'- [x] shipped\n- [ ] pending'}</Markdown>)

  const boxes = screen.container.querySelectorAll('input[type="checkbox"]')
  expect(boxes).toHaveLength(2)
  expect(boxes[0]).toHaveProperty('checked', true)
})

test('links open in a new tab', async () => {
  const screen = await render(<Markdown>{'[docs](https://example.com)'}</Markdown>)

  const link = screen.getByRole('link', { name: 'docs' }).element()
  expect(link.getAttribute('target')).toBe('_blank')
  expect(link.getAttribute('rel')).toContain('noreferrer')
})

test('blank source renders a muted dash', async () => {
  const screen = await render(<Markdown>{'   '}</Markdown>)

  await expect.element(screen.getByText('-')).toBeVisible()
})

screenshotStories(stories)
