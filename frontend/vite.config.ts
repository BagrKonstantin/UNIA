import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // or '0.0.0.0'
    hmr: {
      host: '192.168.178.79', // Put your computer's IP address here
    },
  },
})
