import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { KeyValue } from './KeyValue'
import * as stories from './KeyValue.stories'
import { screenshotStories } from '../test/screenshots'

test('pairs terms with definitions and dashes empty values', async () => {
  const screen = await render(<KeyValue items={[['Region', 'West Europe'], ['Owner', null]]} />)

  await expect.element(screen.getByText('Region')).toBeVisible()
  await expect.element(screen.getByText('West Europe')).toBeVisible()
  await expect.element(screen.getByText('-')).toHaveClass('y-kv-empty')
})

screenshotStories(stories)
