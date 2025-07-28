// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // FE calls /api/...; proxy strips /api and forwards to FastAPI
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''), // <-- important
      },
      // Static media passthrough (no rewrite needed)
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})