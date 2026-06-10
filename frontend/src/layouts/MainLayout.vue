<template>
  <el-container class="h-screen">
    <el-aside width="248px" class="bg-slate-900 text-white">
      <div class="p-4 font-semibold tracking-tight">intelliOffice</div>
      <el-menu
        :default-active="$route.path"
        :default-openeds="defaultOpeneds"
        class="border-none bg-slate-900"
        text-color="#cbd5e1"
        active-text-color="#fff"
        router
      >
        <el-sub-menu v-for="group in navGroups" :key="group.key" :index="group.key">
          <template #title>{{ group.label }}</template>
          <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
            {{ item.label }}
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="flex items-center justify-between border-b border-slate-200 bg-white">
        <span class="text-slate-600">{{ subtitle }}</span>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-500">{{ auth.email }}</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="bg-slate-50">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navGroups = [
  {
    key: 'workspace',
    label: '工作台',
    items: [
      { path: '/', label: '仪表盘' },
      { path: '/demo-walkthrough', label: '演示流程' },
      { path: '/system-health', label: '系统健康' },
    ],
  },
  {
    key: 'customer-development',
    label: '客户开发',
    items: [
      { path: '/companies', label: '公司' },
      { path: '/contacts', label: '联系人' },
      { path: '/lead-intelligence', label: '线索智能工作台' },
      { path: '/growth-operations', label: '增长运营' },
      { path: '/lead-intake', label: '线索录入' },
      { path: '/leads', label: '线索列表' },
      { path: '/tasks', label: '任务' },
      { path: '/field-visits', label: '拜访记录' },
    ],
  },
  {
    key: 'products-quotes',
    label: '产品与报价',
    items: [
      { path: '/products', label: '产品库' },
      { path: '/quote-catalog', label: '报价目录' },
      { path: '/pricing-preview', label: '价格预览' },
      { path: '/quotes', label: '报价单' },
      { path: '/quotes/new', label: '新建报价' },
      { path: '/rfqs', label: 'RFQ' },
      { path: '/samples', label: '样品' },
      { path: '/container-calculator', label: '装柜计算' },
    ],
  },
  {
    key: 'orders-delivery',
    label: '订单交付',
    items: [
      { path: '/orders', label: '订单' },
      { path: '/partner-operations', label: '交付协同' },
      { path: '/portal-integration', label: '生产与物流摘要' },
    ],
  },
  {
    key: 'customer-portal',
    label: '客户 Portal',
    items: [
      { path: '/portal-operations', label: 'Portal 运营' },
      { path: '/portal-customer-bridge', label: 'Portal 联调 UAT' },
      { path: '/feedback-tickets', label: '客户反馈' },
    ],
  },
  {
    key: 'market-response',
    label: '市场响应',
    items: [
      { path: '/market-response', label: '市场响应' },
      { path: '/market-intelligence', label: '市场信号预览' },
    ],
  },
  {
    key: 'partners',
    label: 'Partner 管理',
    items: [
      { path: '/partner-onboarding', label: 'Partner 接入' },
      { path: '/manufacturing-partners', label: '制造伙伴' },
      { path: '/partner-operations', label: '分单与供应商确认' },
    ],
  },
  {
    key: 'demo-docs',
    label: '演示与资料',
    items: [
      { path: '/knowledge-base', label: '资料库' },
      { path: '/ai-assistant', label: 'AI 助手' },
      { path: '/ai-outputs', label: 'AI 输出' },
    ],
  },
] as const

const routeTitles = new Map<string, string>(
  navGroups.flatMap((group) => group.items.map((item) => [item.path, item.label] as const)),
)

const defaultOpeneds = computed(() => {
  const currentPath = route.path
  const group = navGroups.find((candidate) =>
    candidate.items.some((item) => currentPath === item.path || (item.path !== '/' && currentPath.startsWith(`${item.path}/`))),
  )
  return group ? [group.key] : ['workspace']
})

const subtitle = computed(() => routeTitles.get(route.path) || (route.name as string) || '')

function logout() {
  auth.clear()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.el-menu {
  --el-menu-bg-color: #0f172a;
  --el-menu-hover-bg-color: #1e293b;
}

.el-menu-item.is-active {
  background: #1e293b !important;
}
</style>
