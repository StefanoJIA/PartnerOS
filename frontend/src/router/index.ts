import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/desktop-launch',
      name: 'desktop-launch',
      component: () => import('@/pages/desktop/DesktopLaunchPage.vue'),
      meta: { public: true },
    },
    { path: '/login', name: 'login', component: () => import('@/pages/auth/LoginPage.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: () => import('@/pages/dashboard/DashboardPage.vue') },
        { path: 'system-health', name: 'system-health', component: () => import('@/pages/system/SystemHealthPage.vue') },
        { path: 'portal-consumer-mock', name: 'portal-consumer-mock', component: () => import('@/pages/system/PortalConsumerMockPage.vue') },
        { path: 'lead-intelligence', name: 'lead-intelligence', component: () => import('@/pages/leads/LeadIntelligenceWorkbenchPage.vue') },
        { path: 'lead-intake', name: 'lead-intake', component: () => import('@/pages/leads/LeadIntakePage.vue') },
        { path: 'companies', name: 'companies', component: () => import('@/pages/companies/CompaniesPage.vue') },
        { path: 'companies/:companyId', name: 'company-detail', component: () => import('@/pages/companies/CompanyDetailPage.vue') },
        { path: 'contacts', name: 'contacts', component: () => import('@/pages/contacts/ContactsPage.vue') },
        { path: 'contacts/:contactId', name: 'contact-detail', component: () => import('@/pages/contacts/ContactDetailPage.vue') },
        { path: 'leads', name: 'leads', component: () => import('@/pages/leads/LeadsPage.vue') },
        { path: 'leads/:leadId', name: 'lead-detail', component: () => import('@/pages/leads/LeadDetailPage.vue') },
        { path: 'interactions', name: 'interactions', component: () => import('@/pages/placeholders/GenericPlaceholder.vue'), props: { title: 'Interactions' } },
        { path: 'tasks', name: 'tasks', component: () => import('@/pages/tasks/TasksPage.vue') },
        { path: 'outreach/linkedin', name: 'outreach-linkedin', component: () => import('@/pages/ai/AiAssistantPage.vue') },
        { path: 'outreach/email', name: 'outreach-email', component: () => import('@/pages/ai/AiAssistantPage.vue') },
        { path: 'field-visits', name: 'field-visits', component: () => import('@/pages/field/FieldVisitsPage.vue') },
        { path: 'manufacturing-partners', name: 'partners', component: () => import('@/pages/partners/PartnersPage.vue') },
        { path: 'manufacturing-partners/:partnerId', name: 'partner-detail', component: () => import('@/pages/partners/PartnerDetailPage.vue') },
        { path: 'products', name: 'products', component: () => import('@/pages/products/ProductsPage.vue') },
        { path: 'products/:productId', name: 'product-detail', component: () => import('@/pages/products/ProductDetailPage.vue') },
        { path: 'rfqs', name: 'rfqs', component: () => import('@/pages/rfq/RfqsPage.vue') },
        { path: 'rfqs/:rfqId', name: 'rfq-detail', component: () => import('@/pages/rfq/RfqDetailPage.vue') },
        { path: 'samples', name: 'samples', component: () => import('@/pages/samples/SamplesPage.vue') },
        { path: 'samples/:sampleId', name: 'sample-detail', component: () => import('@/pages/samples/SampleDetailPage.vue') },
        { path: 'orders', name: 'orders', component: () => import('@/pages/orders/OrdersPage.vue') },
        { path: 'orders/:orderId', name: 'order-detail', component: () => import('@/pages/orders/OrderDetailPage.vue') },
        { path: 'ai-assistant', name: 'ai-assistant', component: () => import('@/pages/ai/AiAssistantPage.vue') },
        { path: 'ai-outputs', name: 'ai-outputs', component: () => import('@/pages/ai/AiOutputsPage.vue') },
        { path: 'knowledge-base', name: 'knowledge', component: () => import('@/pages/knowledge/KnowledgePage.vue') },
        { path: 'market-intelligence', name: 'market', component: () => import('@/pages/market/MarketPage.vue') },
        { path: 'container-calculator', name: 'container-calc', component: () => import('@/pages/tools/ContainerCalcPage.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/pages/placeholders/GenericPlaceholder.vue'), props: { title: 'Settings' } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (to.meta.requiresAuth && !auth.token) return { name: 'login' }
  return true
})

export default router
