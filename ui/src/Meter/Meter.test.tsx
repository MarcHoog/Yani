import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Meter } from './Meter'
import * as stories from './Meter.stories'
import { screenshotStories } from '../test/screenshots'

test('exposes progress and warns past the threshold', async () => {
  const screen = await render(<Meter value={58} max={60} label="Seats" />)

  const bar = screen.getByRole('progressbar', { name: 'Seats' })
  await expect.element(bar).toHaveAttribute('aria-valuenow', '58')
  await expect.element(bar).toHaveClass('y-meter--warn')
})

test('stays calm below the threshold', async () => {
  const screen = await render(<Meter value={10} max={60} label="Seats" />)

  await expect.element(screen.getByRole('progressbar', { name: 'Seats' })).not.toHaveClass('y-meter--warn')
})

screenshotStories(stories)
