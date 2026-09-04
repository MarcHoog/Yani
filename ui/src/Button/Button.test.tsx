import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { Button } from './Button'
import * as stories from './Button.stories'
import { screenshotStories } from '../test/screenshots'

test('calls onClick and defaults to type button', async () => {
  const onClick = vi.fn()
  const screen = await render(<Button onClick={onClick}>Go</Button>)

  const button = screen.getByRole('button', { name: 'Go' })
  await expect.element(button).toHaveAttribute('type', 'button')
  await button.click()

  expect(onClick).toHaveBeenCalledOnce()
})

test('disabled button ignores clicks', async () => {
  const onClick = vi.fn()
  const screen = await render(
    <Button disabled onClick={onClick}>
      Go
    </Button>,
  )

  await screen.getByRole('button', { name: 'Go' }).click({ force: true })

  expect(onClick).not.toHaveBeenCalled()
})

screenshotStories(stories)
