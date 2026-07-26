import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const siteDir = new URL('../public/site/', import.meta.url)
const rootDir = new URL('../', import.meta.url)
const htmlFiles = readdirSync(siteDir).filter((name) => name.endsWith('.html')).sort()

const requiredPages = [
  'index.html',
  'about.html',
  'service-history.html',
  'services.html',
  'manufacturers.html',
  'partners.html',
  'products.html',
  'reference-center.html',
  'inventory.html',
  'dashboard.html',
]

const publicRoutes = [
  '/',
  '/about',
  '/service-history',
  '/services',
  '/manufacturers',
  '/partners',
  '/login',
  '/change-password',
  '/products',
  '/dashboard',
  '/inventory',
  '/new-order',
  '/reference-center',
  '/customer-service',
  '/order-detail',
  '/product-detail',
  '/user-manual',
  '/product-models',
  '/order-tracking-en',
  '/cart',
  '/order-tracking',
  '/custom-product-request',
  '/order-swatch-set',
  '/product-models-hand-controls',
  '/product-models-accessories',
]


const publicStoryPages = new Set(['index.html', 'about.html', 'service-history.html', 'services.html', 'manufacturers.html', 'partners.html'])
const themeRequiredPages = new Set([
  ...publicStoryPages,
  'cart.html',
  'customer-service.html',
  'custom-product-request.html',
  'dashboard.html',
  'inventory.html',
  'new-order.html',
  'order-detail.html',
  'order-swatch-set.html',
  'product-detail.html',
  'product-models.html',
  'product-models-accessories.html',
  'product-models-hand-controls.html',
  'products.html',
  'reference-center.html',
  'user-manual.html',
])
const portalFlowPages = new Set(['products.html', 'inventory.html', 'reference-center.html', 'dashboard.html'])
const portalFlowLabels = ['Supplier products', 'Local samples', 'Approved resources', 'Customer workspace']
const authPages = new Set(['login.html', 'change-password.html'])
const workspacePages = new Set([
  'cart.html',
  'customer-service.html',
  'custom-product-request.html',
  'dashboard.html',
  'inventory.html',
  'new-order.html',
  'order-detail.html',
  'order-swatch-set.html',
  'order-tracking.html',
  'order-tracking-en.html',
  'product-detail.html',
  'product-models.html',
  'product-models-accessories.html',
  'product-models-hand-controls.html',
  'products.html',
  'reference-center.html',
  'user-manual.html',
])
const forbidden = [
  'Product & Order Portal',
  'Chongqing Huiju',
  'Huiju',
  '??',
  '??',
  'JOOBOO',
  'JOOBO',
  'internal PartnerOS execution',
  'PartnerOS execution',
  'partner data is approved',
  'partner products',
  'Catalog by partner',
  'partner program',
  'Internal costs',
  'raw tokens',
  'backend file paths',
  'backend paths',
  'supplier private notes',
  'internal-only operating comments',
  'DOoTYPE',
  'US-ohina',
  '#52657o',
  'costs and margins',
  '<div class="header">',
  '<div class="header portal-header">',
  '<div class="header-content portal-header-inner">',
  '<header class="site-header">',
  '<footer class="footer">',
]


const forbiddenHtmlSnippets = [
  '>Company</a>',
  '<h3>Company</h3>',
  'Track Orders',
  'Order Tracking System',
  'Track your order progress in real-time',
  'href="/partners',
  'site-pathway-section',
  'site-pathway-card',
  'workspace-gateway',
  'workspace-gateway-card',
  'JSOe',
  'iseae',
  'mobileeav',
  'resource-hub-grid',
  'workspace-route-strip',
  'site-mode-nav',
  'site-mode-link',
  'workspace-mode-nav',
  'Deeper path',
  'supplier-section',
  'supplier-grid',
  'supplier-card',
  'supplier-badge',
  'supplier-name',
  'supplier-desc',
  'Loading items',
  'Loading tracking information',
  'getOrder status',
  'shippingOrder status',
  'orderOrder status',
]

const workspaceContextPages = new Set([
  'cart.html',
  'new-order.html',
  'order-detail.html',
  'order-tracking.html',
  'order-tracking-en.html',
  'customer-service.html',
  'custom-product-request.html',
  'product-detail.html',
  'product-models.html',
  'product-models-accessories.html',
  'product-models-hand-controls.html',
  'order-swatch-set.html',
  'user-manual.html',
])
const workspaceFlowPages = new Set(['cart.html', 'new-order.html', 'order-detail.html', 'customer-service.html'])
const workspaceFlowLabels = ['Product review', 'Selected products', 'Create order', 'Order progress', 'Support']
const productDecisionPages = new Set([
  'product-detail.html',
  'product-models.html',
  'product-models-hand-controls.html',
  'product-models-accessories.html',
  'order-swatch-set.html',
  'user-manual.html',
  'custom-product-request.html',
])
const productDecisionLabels = ['Supplier program', 'Product options', 'Samples & resources', 'Selected products', 'Order workspace']
const requiredContent = new Map([
  ['order-detail.html', ['Order progress detail', 'Production and shipment progress', 'Customer-safe order progress', 'Customer-safe production and shipment updates', 'Product review', 'Selected products', 'Create order', 'Support']],
  ['change-password.html', ['Change Password', 'Security notice', 'Current password', 'New password', 'Confirm new password', 'Customer Workspace', 'auth-footer']],
  ['index.html', ['Connect. Source. Deliver.', 'bridge-flow-section', 'Market side', 'IntelliOpus role', 'Manufacturer side', 'site-journey-ribbon', 'About IntelliOpus', 'Service model', 'Manufacturers', 'Catalog & resources', 'Customer workspace', 'id="site-reading-path"', 'How to use this site', 'Understand IntelliOpus', 'See the service history', 'Review the operating loop', 'Compare supplier programs', 'Browse product programs', 'Continue after sign-in', 'JOBO education furniture is active']],  ['about.html', ['Company overview', 'Service history', 'id="operating-history"', 'id="operating-bridge"', 'id="customer-workspace-path"', 'id="operating-principles"', 'Supplier-neutral entry', 'Customer-safe workspace', 'public-page-summary', 'Position', 'Scope', 'Customer Workspace', 'HOSUN', 'JOBO', 'page-transition-strip', 'Company role', 'next-step-panel', 'Supplier network', 'Product programs', 'Resources', 'Local samples']],
  ['service-history.html', ['Service history', 'id="service-history-overview"', 'id="history-timeline"', 'id="history-lessons"', 'id="history-workspace-path"', 'HOSUN product path', 'JOBO education furniture', 'Supplier-neutral IntelliOpus', 'page-transition-strip', 'Real quote and order work', 'next-step-panel', 'Supplier network', 'Product programs', 'Resources', 'Customer workspace']],
  ['services.html', ['Quote support', 'Approved customer visibility', 'From first review to customer workspace', 'id="operating-loop"', 'Demand intake', 'Supplier fit', 'Quote and sample decision', 'id="connected-workflow"', 'id="safety-boundary"', 'id="service-workspace-path"', 'public-page-summary', 'Discover', 'Coordinate', 'Improve', 'Supplier expansion', 'page-transition-strip', 'Service model', 'next-step-panel', 'Product programs', 'Resources', 'Local samples']],
  ['manufacturers.html', ['HOSUN lifting systems', 'JOBO education furniture', 'Future supplier programs', 'supplier-future-card', 'customer-safe fields', 'Qualified suppliers, connected through one IntelliOpus path', 'Peer suppliers', 'Separate product rules', 'One customer path', 'Current supplier programs', 'Different product models', 'id="supplier-workspace-path"', 'id="supplier-program-map"', 'How the network works', 'Internal side', 'From supplier program to customer workspace', 'Resources', 'Local samples']],
  ['partners.html', ['HOSUN lifting systems', 'JOBO education furniture', 'Future supplier programs', 'supplier-future-card', 'customer-safe fields', 'Qualified suppliers, connected through one IntelliOpus path', 'Peer suppliers', 'Separate product rules', 'One customer path', 'Current supplier programs', 'Different product models', 'id="supplier-workspace-path"', 'id="supplier-program-map"', 'How the network works', 'Internal side', 'From supplier program to customer workspace', 'Resources', 'Local samples']],
  ['products.html', ['Product Programs', 'portal-showcase-hero', 'id="hosun"', 'id="jobo"', 'Supplier programs for product selection', 'Approved supplier programs', 'catalog-page-summary', 'portal-flow-intro', 'Customer path', 'Sign in to view selectable model families', 'partner-program-section', 'id="supplier-programs"', 'functional-focus-strip', 'Product review', 'Choose the supplier program first', 'Local samples']],
  ['reference-center.html', ['Resources', 'portal-showcase-hero', 'Approved resources for product decisions', 'Official RAL website', 'Download RAL guide', 'Color confirmation', 'Supplier resources', 'Order support', 'HOSUN lifting systems', 'JOBO education furniture', 'brand-resource-section', 'id="ral"', 'id="hosun-resources"', 'id="jobo-resources"', 'resource-program-map', 'Universal color references', 'Future supplier resources', 'future-resources', 'functional-focus-strip', 'Resource review', 'Use approved files']],
  ['inventory.html', ['Local samples', 'Sample workflow', 'JOBO', 'Future suppliers', 'workspace-context-band', 'workspace-page-summary', 'Supplier-separated stock', 'functional-focus-strip', 'Sample review', 'Check local samples', 'Product programs', 'Resources']],
  ['dashboard.html', ['Customer order workspace', 'Customer Workspace', 'workspace-context-band', 'workspace-page-summary', 'Product and sample path', 'Customer workspace', 'portal-flow-intro', 'Workspace path', 'id="workspace-journey"', 'Workspace scope', 'Orders, samples, resources, and support stay together', 'functional-focus-strip', 'Workspace use', 'Continue after product review', 'Resources', 'Local samples']],
  ['order-tracking.html', ['Order status now lives inside the customer workspace', 'Workspace compatibility path', 'One order area', 'Customer-safe view', 'Supplier coordination stays internal']],
  ['order-tracking-en.html', ['Order status now lives inside the customer workspace', 'Workspace compatibility path', 'One order area', 'Customer-safe view', 'Supplier coordination stays internal']],
])

const failures = []
const read = (url) => readFileSync(url, 'utf8')

for (const page of requiredPages) {
  if (!htmlFiles.includes(page)) failures.push(`missing required page: ${page}`)
}

for (const page of htmlFiles) {
  const text = read(new URL(page, siteDir))
  const title = text.match(/<title>(.*?)<\/title>/s)?.[1] || ''
  if (!title.includes('IntelliOpus') || !title.includes('Portal')) failures.push(`${page}: title is not IntelliOpus Portal: ${title}`)
  if (themeRequiredPages.has(page) && !text.includes('/css/customer-theme.css')) failures.push(`${page}: missing shared customer theme stylesheet`)
  if (!text.includes('portal-footer')) failures.push(`${page}: missing unified footer`)
  if (workspacePages.has(page) && !text.includes('portal-context-band')) {
    failures.push(`${page}: workspace page missing portal context band`)
  }
  if (publicStoryPages.has(page) && page !== 'index.html' && !text.includes('company-hero')) {
    failures.push(`${page}: public story page missing company hero`)
  }
  if (publicStoryPages.has(page) && page !== 'index.html' && text.includes('<style')) {
    failures.push(`${page}: public story page should use shared theme CSS, not inline styles`)
  }
  if (authPages.has(page) && !text.includes('auth-site-strip')) {
    failures.push(`${page}: auth page missing public site navigation strip`)
  }
  if (!authPages.has(page) && !text.includes('portal-header')) {
    failures.push(`${page}: missing unified portal header`)
  }
  if (workspaceContextPages.has(page) && !text.includes('workspace-context-band')) {
    failures.push(`${page}: missing workspace context band`)
  }
  if (workspaceFlowPages.has(page)) {
    if (!text.includes('workspace-path-mini')) failures.push(`${page}: missing compact customer workspace path`)
    for (const label of workspaceFlowLabels) {
      if (!text.includes(label)) failures.push(`${page}: missing workspace path label: ${label}`)
    }
  }
  if (productDecisionPages.has(page)) {
    if (!text.includes('product-decision-path')) failures.push(`${page}: missing product decision path`)
    for (const label of productDecisionLabels) {
      if (!text.includes(label)) failures.push(`${page}: missing product decision path label: ${label}`)
    }
  }
  if (!authPages.has(page) && !text.includes('href="/products">Product Programs')) {
    failures.push(`${page}: missing product catalog navigation`)
  }
  if (!authPages.has(page) && !text.includes('portal-workspace-menu')) {
    failures.push(`${page}: missing workspace menu`)
  }
  if (text.includes('images.unsplash.com')) {
    for (const imagePart of text.split('<img')) {
      const imageTag = imagePart.split('>', 1)[0]
      if (imageTag.includes('images.unsplash.com') && !imageTag.includes('onerror=')) {
        failures.push(`${page}: external image missing local fallback`)
      }
    }
  }
  if (text.includes('<div id="welcomeUser"') && text.includes('<a href="/dashboard" class="btn btn-secondary">Dashboard</a>')) {
    failures.push(`${page}: duplicate dashboard shortcut inside signed-in user controls`)
  }
  for (const word of forbidden) {
    if (text.includes(word)) failures.push(`${page}: forbidden legacy/customer wording found: ${word}`)
  }
  for (const snippet of forbiddenHtmlSnippets) {
    if (text.includes(snippet)) failures.push(`${page}: forbidden legacy/html snippet found: ${snippet}`)
  }
  for (const [target, needles] of requiredContent.entries()) {
    if (page !== target) continue
    for (const needle of needles) {
      if (!text.includes(needle)) failures.push(`${page}: missing required content: ${needle}`)
    }
  }
}

const vite = read(new URL('vite.config.ts', rootDir))
const nginx = read(new URL('nginx.local-server.conf', rootDir))
const localServer = read(new URL('../scripts/customer_portal_local_server.py', rootDir))
if (!vite.includes(`'/manufacturers': '/site/manufacturers.html'`)) failures.push('vite manufacturers route points to the wrong page')
if (!vite.includes(`'/partners': '/site/manufacturers.html'`)) failures.push('vite partners route should be a compatibility alias for manufacturers')
if (!nginx.includes('try_files /site/manufacturers.html /site/index.html')) failures.push('nginx manufacturers route points to the wrong page')
for (const route of publicRoutes) {
  const routeKey = route === '/' ? "'/': '/site/index.html'" : `'${route}': '/site/${route.slice(1)}.html'`
  if (route !== '/' && !vite.includes(`'${route}':`)) failures.push(`vite route missing: ${route}`)
  if (route === '/' && !vite.includes(routeKey)) failures.push('vite route missing: /')
  if (route !== '/' && !nginx.includes(route.slice(1))) failures.push(`nginx route missing: ${route}`)
}

if (failures.length) {
  console.error('Customer portal site check failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log(`Customer portal site check passed: ${htmlFiles.length} pages, ${publicRoutes.length} public routes.`)























