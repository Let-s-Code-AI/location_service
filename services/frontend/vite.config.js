import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The backend has no CORS configured, so in dev we proxy /api/* to it.
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    // globals: Testing Library auto-cleanup between tests needs a global afterEach.
    globals: true,
    // `npm run test:coverage` (CI quality gate). Only application code counts;
    // the entry point just mounts <App /> and is not unit-tested.
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/**/*.test.{js,jsx}', 'src/main.jsx'],
      reporter: ['text', 'lcov'],
      // Floor just under the current numbers (App.jsx, Login.jsx and api.js
      // have no unit tests yet). Raise these as tests are added.
      thresholds: { statements: 40, branches: 40, functions: 35, lines: 40 },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
