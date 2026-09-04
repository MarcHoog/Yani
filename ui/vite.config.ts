/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { playwright } from '@vitest/browser-playwright'

export default defineConfig({
  plugins: [react()],
  test: {
    include: ['src/**/*.test.tsx'],
    setupFiles: ['./src/test/setup.ts'],
    browser: {
      enabled: true,
      headless: true,
      provider: playwright(),
      viewport: { width: 1024, height: 900 },
      instances: [{ browser: 'chromium' }],
    },
  },
})
