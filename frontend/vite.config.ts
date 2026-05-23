import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const host = process.env.TAURI_DEV_HOST
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

/** Tauri injects TAURI_ENV_* when running beforeDevCommand / beforeBuildCommand (see Tauri CLI schema). */
const tauriHook = Boolean(process.env.TAURI_ENV_PLATFORM)

// https://v2.tauri.app/start/frontend/vite/
export default defineConfig({
  clearScreen: false,
  plugins: [vue()],
  envPrefix: ['VITE_', 'TAURI_ENV_*'],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: host || true,
    port: 5173,
    strictPort: tauriHook,
    hmr: host
      ? {
          protocol: 'ws',
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/health': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  build: process.env.TAURI_ENV_PLATFORM
    ? {
        target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
        minify: process.env.TAURI_ENV_DEBUG ? false : 'esbuild',
        sourcemap: !!process.env.TAURI_ENV_DEBUG,
      }
    : {},
})
