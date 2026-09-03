import { beforeEach, expect, test } from 'vitest'
import { render, renderHook } from 'vitest-browser-react'
import { ThemeToggle, useTheme } from './ThemeToggle'
import * as stories from './ThemeToggle.stories'
import { screenshotStories } from '../test/screenshots'

const osTheme = () => (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')

beforeEach(() => localStorage.removeItem('theme'))

test('follows the OS when nothing is stored', async () => {
  const { result } = await renderHook(() => useTheme())

  expect(result.current.preference).toBe('system')
  expect(result.current.resolved).toBe(osTheme())
  expect(document.documentElement.dataset.theme).toBe(osTheme())
})

test('toggling stores an explicit choice', async () => {
  localStorage.setItem('theme', 'light')
  const screen = await render(<ThemeToggle />)

  await screen.getByRole('button', { name: 'Switch to dark mode' }).click()
  expect(localStorage.getItem('theme')).toBe('dark')
  expect(document.documentElement.dataset.theme).toBe('dark')

  await screen.getByRole('button', { name: 'Switch to light mode' }).click()
  expect(localStorage.getItem('theme')).toBe('light')
  expect(document.documentElement.dataset.theme).toBe('light')
})

test('every toggle on the page follows the same choice', async () => {
  localStorage.setItem('theme', 'light')
  const screen = await render(
    <>
      <ThemeToggle />
      <ThemeToggle />
    </>,
  )

  await screen.getByRole('button', { name: 'Switch to dark mode' }).first().click()

  await expect.element(screen.getByRole('button', { name: 'Switch to light mode' }).nth(1)).toBeVisible()
  expect(screen.getByRole('button', { name: 'Switch to light mode' }).elements()).toHaveLength(2)
})

test('set(system) clears the stored choice', async () => {
  localStorage.setItem('theme', 'dark')
  const { result, act } = await renderHook(() => useTheme())

  await act(() => result.current.set('system'))

  expect(localStorage.getItem('theme')).toBeNull()
  expect(result.current.resolved).toBe(osTheme())
})

screenshotStories(stories)
