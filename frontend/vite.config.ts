import { defineConfig } from 'vite'
import type { Plugin, ViteDevServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const host = process.env.TAURI_DEV_HOST
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8010'

/** Tauri injects TAURI_ENV_* when running beforeDevCommand / beforeBuildCommand (see Tauri CLI schema). */
const tauriHook = Boolean(process.env.TAURI_ENV_PLATFORM)
const customerSiteEnabled = process.env.VITE_CUSTOMER_SITE_ENABLED === 'true'

const customerSiteRoutes: Record<string, string> = {
  '/': '/site/index.html',
  '/about': '/site/about.html',
  '/service-history': '/site/service-history.html',
  '/services': '/site/services.html',
  '/manufacturers': '/site/manufacturers.html',
  '/partners': '/site/manufacturers.html',
  '/login': '/site/login.html',
  '/change-password': '/site/change-password.html',
  '/products': '/site/products.html',
  '/dashboard': '/site/dashboard.html',
  '/inventory': '/site/inventory.html',
  '/new-order': '/site/new-order.html',
  '/reference-center': '/site/reference-center.html',
  '/customer-service': '/site/customer-service.html',
  '/order-detail': '/site/order-detail.html',
  '/product-detail': '/site/product-detail.html',
  '/user-manual': '/site/user-manual.html',
  '/product-models': '/site/product-models.html',
  '/order-tracking-en': '/site/order-tracking-en.html',
  '/cart': '/site/cart.html',
  '/order-tracking': '/site/order-tracking.html',
  '/custom-product-request': '/site/custom-product-request.html',
  '/order-swatch-set': '/site/order-swatch-set.html',
  '/product-models-hand-controls': '/site/product-models-hand-controls.html',
  '/product-models-accessories': '/site/product-models-accessories.html',
}

function customerSiteDevRoutes(): Plugin {
  return {
    name: 'customer-site-dev-routes',
    configureServer(server: ViteDevServer) {
      server.middlewares.use((req, _res, next) => {
        if (!req.url || !['GET', 'HEAD'].includes(req.method || 'GET')) {
          next()
          return
        }
        const parsed = new URL(req.url, 'http://localhost')
        const direct = customerSiteRoutes[parsed.pathname]
        const prefix = parsed.pathname.match(/^\/(product-models|product-detail|order-detail|order-tracking)\//)?.[1]
        const target = direct || (prefix ? `/site/${prefix}.html` : undefined)
        if (target) {
          req.url = `${target}${parsed.search}`
        }
        next()
      })
    },
  }
}

// https://v2.tauri.app/start/frontend/vite/
export default defineConfig({
  clearScreen: false,
  plugins: [customerSiteEnabled ? customerSiteDevRoutes() : null, vue()].filter(Boolean),
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
  build: {
    minify: false,
    reportCompressedSize: false,
    rollupOptions: {
      onwarn(warning, warn) {
        if (warning.message.includes('is dynamically imported by') && warning.message.includes('src/api/http.ts')) {
          return
        }
        warn(warning)
      },
    },
    ...(process.env.TAURI_ENV_PLATFORM
      ? {
          target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
          minify: process.env.TAURI_ENV_DEBUG ? false : 'esbuild',
          sourcemap: !!process.env.TAURI_ENV_DEBUG,
        }
      : {}),
  },
})


