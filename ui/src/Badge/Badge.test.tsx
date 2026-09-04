import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Badge } from './Badge'
import * as stories from './Badge.stories'
import { screenshotStories } from '../test/screenshots'

test('renders the tone as a class', async () => {
  const screen = await render(<Badge tone="danger">Disabled</Badge>)

  await expect.element(screen.getByText('Disabled')).toHaveClass('y-badge--danger')
})

screenshotStories(stories)
