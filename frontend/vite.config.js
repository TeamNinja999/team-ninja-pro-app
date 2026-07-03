import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:5000' },
    watch: {
      usePolling: true, // Forces Vite to constantly check for file changes
      interval: 100 // Checks every 100ms
    }
  },
  build: {
    outDir: 'build',
    emptyOutDir: true
  }
})