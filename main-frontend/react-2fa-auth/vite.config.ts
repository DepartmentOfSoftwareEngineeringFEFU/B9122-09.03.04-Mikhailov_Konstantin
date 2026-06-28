import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/predictions': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/v1/profile': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})