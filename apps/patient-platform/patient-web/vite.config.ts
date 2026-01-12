import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react()],
    server: {
      host: 'localhost',
      port: 5173,
      cors: true,
      proxy: {
        '/api': {
          target: env.VITE_GATEWAY_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          ws: true,
        }
      }
    },
    define: {
      global: 'globalThis',
    }
  }
})