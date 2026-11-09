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
