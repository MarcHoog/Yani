import { expect, test } from 'vitest'
import { render } from 'vitest-browser-react'
import { Field, Input, Select } from './Field'
import * as stories from './Field.stories'
import { screenshotStories } from '../test/screenshots'

test('label names the control', async () => {
  const screen = await render(
    <Field label="Work email" hint="Used for sign-in">
      <Input type="email" />
    </Field>,
  )

  await expect.element(screen.getByRole('textbox', { name: /Work email/ })).toBeVisible()
  await expect.element(screen.getByText('Used for sign-in')).toBeVisible()
})

test('error replaces the hint', async () => {
  const screen = await render(
    <Field label="Site" hint="Pick one" error="Required">
      <Select>
        <option>Gent</option>
      </Select>
    </Field>,
  )

  await expect.element(screen.getByText('Required')).toBeVisible()
  await expect.element(screen.getByText('Pick one')).not.toBeInTheDocument()
})

screenshotStories(stories)
