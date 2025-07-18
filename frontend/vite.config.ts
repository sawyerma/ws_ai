import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      '/api':       'http://localhost:8000',
      '/ohlc':      'http://localhost:8000',
      '/orderbook': 'http://localhost:8000',
      '/symbols':   'http://localhost:8000'
    }
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src"
    },
  },
})
