import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './', // CRITICAL: Fixes ERR_FILE_NOT_FOUND in Electron compiled .exe
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:5000' },
    watch: {
      usePolling: true,
      interval: 100
    }
  },
  build: {
    outDir: 'build',
    emptyOutDir: true
  }
})