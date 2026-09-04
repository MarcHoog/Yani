import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Table } from './Table'
import * as stories from './Table.stories'
import { screenshotStories } from '../test/screenshots'

test('renders a dash for missing cells', async () => {
  const screen = await render(<Table columns={['Name', 'Title']} rows={[['Els', null]]} />)

  await expect.element(screen.getByRole('cell', { name: '-' })).toBeVisible()
})

test('shows the empty message when there are no rows', async () => {
  const screen = await render(<Table columns={['Name']} rows={[]} empty="No people" />)

  await expect.element(screen.getByRole('cell', { name: 'No people' })).toHaveAttribute('colspan', '1')
})

screenshotStories(stories)
