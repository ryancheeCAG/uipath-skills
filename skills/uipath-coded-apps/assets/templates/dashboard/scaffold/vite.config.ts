import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

function failBuildIfPatSet(): Plugin {
  return {
    name: 'fail-build-if-pat-set',
    apply: 'build',
    buildStart() {
      const pat = process.env.VITE_UIPATH_PAT
      if (pat && pat.length > 0) {
        throw new Error(
          'VITE_UIPATH_PAT is set — remove .env.local before building for production. ' +
          'Production deployments use ActionCenterTokenManager, not a PAT.'
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
      path: 'path-browserify',
    },
  },
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
  },
})
