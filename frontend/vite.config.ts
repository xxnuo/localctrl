import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'https://localhost:2001',
      '/ws': {
        target: 'wss://localhost:2001',
        ws: true,
      },
      '/proxy': 'https://localhost:2001',
    },
  },
})
