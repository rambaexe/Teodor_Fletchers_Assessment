import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Frontend calls /api/*; Vite proxies to the backend (localhost locally, `backend` in docker).
const apiTarget = process.env.API_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
})
