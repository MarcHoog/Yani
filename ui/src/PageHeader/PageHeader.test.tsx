import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { PageHeader } from './PageHeader'
import * as stories from './PageHeader.stories'
import { screenshotStories } from '../test/screenshots'

test('renders the title as the page heading', async () => {
  const screen = await render(<PageHeader title="People" sub="48 accounts" />)

  await expect.element(screen.getByRole('heading', { level: 1, name: 'People' })).toBeVisible()
  await expect.element(screen.getByText('48 accounts')).toBeVisible()
})

screenshotStories(stories)
