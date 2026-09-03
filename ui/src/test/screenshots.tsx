import type { ComponentType } from 'react'
import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'

type Stories = { default: { title: string } } & Record<string, unknown>

export function screenshotStories({ default: meta, ...variants }: Stories) {
  for (const [name, Story] of Object.entries(variants) as [string, ComponentType][]) {
    for (const theme of ['light', 'dark'] as const) {
      test(`${meta.title}/${name} ${theme}`, async () => {
        document.documentElement.dataset.theme = theme
        const screen = await render(<Story />)
        screen.container.style.pointerEvents = 'none'
        await expect(screen.locator).toMatchScreenshot(`${name}-${theme}`)
      })
    }
  }
}
