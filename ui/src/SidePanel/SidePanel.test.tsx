import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { SidePanel } from './SidePanel'
import * as stories from './SidePanel.stories'
import { screenshotStories } from '../test/screenshots'

test('renders title and content when open', async () => {
  const screen = await render(
    <SidePanel open label="Card" title="Ship the board" onClose={() => {}}>
      <p>Card details</p>
    </SidePanel>,
  )

  await expect.element(screen.getByRole('dialog', { name: 'Card' })).toBeVisible()
  await expect.element(screen.getByText('Ship the board')).toBeVisible()
  await expect.element(screen.getByText('Card details')).toBeVisible()
})

test('close button calls onClose', async () => {
  const onClose = vi.fn()
  const screen = await render(
    <SidePanel open label="Card" title="Ship the board" onClose={onClose}>
      <p>Card details</p>
    </SidePanel>,
  )

  await screen.getByRole('button', { name: 'Close' }).click()

  expect(onClose).toHaveBeenCalled()
})

test('pointer down outside the panel calls onClose', async () => {
  const onClose = vi.fn()
  await render(
    <SidePanel open label="Card" title="Ship the board" onClose={onClose}>
      <p>Card details</p>
    </SidePanel>,
  )

  document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))

  expect(onClose).toHaveBeenCalled()
})

test('escape calls onClose', async () => {
  const onClose = vi.fn()
  await render(
    <SidePanel open label="Card" title="Ship the board" onClose={onClose}>
      <p>Card details</p>
    </SidePanel>,
  )

  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))

  expect(onClose).toHaveBeenCalled()
})

test('a closed panel stays out of reach', async () => {
  const onClose = vi.fn()
  const screen = await render(
    <SidePanel open={false} label="Card" title="Ship the board" onClose={onClose}>
      <p>Card details</p>
    </SidePanel>,
  )

  expect(screen.container.querySelector('.y-panel-layer--open')).toBeNull()
  expect(screen.container.querySelector('[inert]')).not.toBeNull()

  document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))

  expect(onClose).not.toHaveBeenCalled()
})

test('fullscreen button toggles the layout', async () => {
  const screen = await render(
    <SidePanel open label="Card" title="Ship the board" onClose={() => {}}>
      <p>Card details</p>
    </SidePanel>,
  )

  await screen.getByRole('button', { name: 'Fullscreen' }).click()

  expect(screen.container.querySelector('.y-panel-layer--full')).not.toBeNull()

  await screen.getByRole('button', { name: 'Leave fullscreen' }).click()

  expect(screen.container.querySelector('.y-panel-layer--full')).toBeNull()
})

screenshotStories(stories)
