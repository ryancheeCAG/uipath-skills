import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

function failBuildIfPatSet(): Plugin {
  return {
    name: 'fail-build-if-pat-set',
    apply: 'build',
    buildStart() {
      const pat = process.env.VITE_UIPATH_PAT
      if (pat && pat.length > 0) {
        throw new Error(
          'VITE_UIPATH_PAT is set — remove .env.local before building for production.'
        )
      }
    },
  }
}

export default defineConfig({
  plugins: [react(), failBuildIfPatSet()],
  base: './',
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
  },
  server: {
    port: Number(process.env.VITE_DEV_PORT ?? 57173),
    strictPort: false,
  },
})
