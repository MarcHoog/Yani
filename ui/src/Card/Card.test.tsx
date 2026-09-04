import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Card } from './Card'
import * as stories from './Card.stories'
import { screenshotStories } from '../test/screenshots'

test('renders the title as a heading', async () => {
  const screen = await render(<Card title="Sites">body</Card>)

  await expect.element(screen.getByRole('heading', { name: 'Sites' })).toBeVisible()
})

screenshotStories(stories)
