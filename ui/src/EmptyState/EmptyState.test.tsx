import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { EmptyState } from './EmptyState'
import * as stories from './EmptyState.stories'
import { screenshotStories } from '../test/screenshots'

test('renders title, text and action', async () => {
  const screen = await render(<EmptyState title="No tickets yet" text="Ask the helpdesk" action={<button type="button">New</button>} />)

  await expect.element(screen.getByText('No tickets yet')).toBeVisible()
  await expect.element(screen.getByText('Ask the helpdesk')).toBeVisible()
  await expect.element(screen.getByRole('button', { name: 'New' })).toBeVisible()
})

screenshotStories(stories)
