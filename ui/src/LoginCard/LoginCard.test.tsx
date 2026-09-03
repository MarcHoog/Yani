import { expect, test, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { LoginCard } from './LoginCard'
import * as stories from './LoginCard.stories'
import { screenshotStories } from '../test/screenshots'

test('submits email, password and remember', async () => {
  const onSubmit = vi.fn()
  const screen = await render(<LoginCard brand="Yani" onSubmit={onSubmit} />)

  await screen.getByLabelText('Email').fill('els@cookiecooker.be')
  await screen.getByLabelText('Password').fill('hunter2')
  await screen.getByLabelText('Remember me on this device').click()
  await screen.getByRole('button', { name: 'Sign in' }).click()

  expect(onSubmit).toHaveBeenCalledWith({ email: 'els@cookiecooker.be', password: 'hunter2', remember: true })
})

test('blocks submit while busy', async () => {
  const onSubmit = vi.fn()
  const screen = await render(<LoginCard brand="Yani" busy onSubmit={onSubmit} />)

  await expect.element(screen.getByRole('button', { name: 'Signing in...' })).toBeDisabled()
  expect(onSubmit).not.toHaveBeenCalled()
})

test('announces the error', async () => {
  const screen = await render(<LoginCard brand="Yani" error="Wrong email or password." onSubmit={() => {}} />)

  await expect.element(screen.getByRole('alert')).toHaveTextContent('Wrong email or password.')
})

screenshotStories(stories)
