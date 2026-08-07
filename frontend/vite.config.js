import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The Google Sign-In popup needs the opener to keep its window handle, which a
// COOP of "same-origin" would sever. Vercel already sets these in vercel.json;
// mirroring them here keeps `vite dev` and `vite preview` behaving like prod.
const crossOriginHeaders = {
  'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
  'Cross-Origin-Embedder-Policy': 'unsafe-none',
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    headers: crossOriginHeaders,
  },
  preview: {
    headers: crossOriginHeaders,
  },
})
