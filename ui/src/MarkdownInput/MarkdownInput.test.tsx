import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { MarkdownInput } from './MarkdownInput'
import * as stories from './MarkdownInput.stories'
import { screenshotStories } from '../test/screenshots'

test('typing reports the new value', async () => {
  const onChange = vi.fn()
  const screen = await render(<MarkdownInput value="" onChange={onChange} placeholder="Describe the card" />)

  await screen.getByPlaceholder('Describe the card').fill('hello')

  expect(onChange).toHaveBeenCalledWith('hello')
})

test('preview renders the markdown', async () => {
  const screen = await render(<MarkdownInput value="**done**" onChange={() => {}} />)

  await screen.getByRole('button', { name: 'Preview' }).click()

  await expect.element(screen.getByText('done')).toBeVisible()
  expect(screen.container.querySelector('textarea')).toBeNull()
})

test('write returns to the textarea', async () => {
  const screen = await render(<MarkdownInput value="**done**" onChange={() => {}} />)

  await screen.getByRole('button', { name: 'Preview' }).click()
  await screen.getByRole('button', { name: 'Write' }).click()

  expect(screen.container.querySelector('textarea')).not.toBeNull()
})

screenshotStories(stories)
