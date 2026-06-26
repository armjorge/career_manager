import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'strip-crossorigin-for-static-hosting',
      transformIndexHtml: {
        order: 'post',
        handler(html) {
          // S3 website hosting does not send CORS headers; crossorigin breaks module loads.
          return html.replace(/\s+crossorigin/g, '')
        },
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
