import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    lib: { entry: 'src/index.ts', formats: ['es'], fileName: 'web-pet' },
    rollupOptions: {},
  },
  test: { environment: 'jsdom', setupFiles: ['src/test-setup.ts'] },
})
