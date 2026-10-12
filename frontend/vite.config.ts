import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/intake': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/cases': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/tts': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/transcribe': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
