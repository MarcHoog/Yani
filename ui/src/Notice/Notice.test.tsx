import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Notice } from './Notice'
import * as stories from './Notice.stories'
import { screenshotStories } from '../test/screenshots'

test('danger notices are alerts, others are status', async () => {
  const screen = await render(
    <>
      <Notice tone="danger">Failed</Notice>
      <Notice tone="success">Saved</Notice>
    </>,
  )

  await expect.element(screen.getByRole('alert')).toHaveTextContent('Failed')
  await expect.element(screen.getByRole('status')).toHaveTextContent('Saved')
})

screenshotStories(stories)
