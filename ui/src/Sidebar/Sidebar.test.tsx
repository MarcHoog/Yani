import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { Sidebar } from './Sidebar'
import * as stories from './Sidebar.stories'
import { screenshotStories } from '../test/screenshots'

const groups = [{ title: 'Helpdesk', items: [{ label: 'Board', href: '/board', active: true }, { label: 'Automations', href: '/automations', badge: 2 }] }]

test('marks the active item', async () => {
  const screen = await render(<Sidebar brand="Yani" groups={groups} />)

  await expect.element(screen.getByRole('link', { name: 'Board' })).toHaveAttribute('aria-current', 'page')
  await expect.element(screen.getByRole('link', { name: 'Automations 2' })).not.toHaveAttribute('aria-current')
})

test('hands navigation to onNavigate instead of following the href', async () => {
  const onNavigate = vi.fn()
  const before = location.href
  const screen = await render(<Sidebar brand="Yani" groups={groups} onNavigate={onNavigate} />)

  await screen.getByRole('link', { name: 'Automations 2' }).click()

  expect(onNavigate).toHaveBeenCalledWith('/automations')
  expect(location.href).toBe(before)
})

screenshotStories(stories)
