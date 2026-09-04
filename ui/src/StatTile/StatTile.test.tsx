import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { StatTile } from './StatTile'
import * as stories from './StatTile.stories'
import { screenshotStories } from '../test/screenshots'

test('marks a bad hint', async () => {
  const screen = await render(<StatTile label="Devices" value={61} hint="2 non-compliant" bad />)

  await expect.element(screen.getByText('2 non-compliant')).toHaveClass('y-stat-hint--bad')
})

screenshotStories(stories)
