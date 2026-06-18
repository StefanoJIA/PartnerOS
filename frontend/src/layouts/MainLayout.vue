<template>
  <el-container class="h-screen">
    <el-aside width="260px" class="app-aside text-white">
      <div class="brand-panel">
        <div class="brand-mark"><IntelliOpusMark /></div>
        <div>
          <div class="brand-name">IntelliOpus</div>
          <div class="brand-subtitle">PartnerOS</div>
        </div>
      </div>
      <el-menu
        :default-active="$route.path"
        :default-openeds="defaultOpeneds"
        class="border-none"
        text-color="#dbeafe"
        active-text-color="#ffffff"
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
import IntelliOpusMark from '@/components/brand/IntelliOpusMark.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navGroups = [
  {
    key: 'workspace',
    label: '工作台',
    items: [
      { path: '/', label: '仪表盘' },
      { path: '/daily-decision-queue', label: '今日决策队列' },
      { path: '/commercial-intelligence', label: '商业智能' },
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
      { path: '/portal-integration', label: 'Portal 运营' },
      { path: '/portal-customer-bridge', label: 'Portal 联调 UAT' },
      { path: '/feedback-tickets', label: '客户反馈' },
    ],
  },
  {
    key: 'market-response',
    label: '市场响应',
    items: [
      { path: '/market-intelligence', label: '市场响应' },
      { path: '/market-response', label: '市场响应入口' },
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
    key: 'execution-docs',
    label: '执行与资料',
    items: [
      { path: '/external-execution', label: '外部执行 / Staging' },
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
.app-aside {
  background: linear-gradient(180deg, #0b2f6b 0%, #0a2454 46%, #071a3a 100%);
}

.brand-panel {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(191, 219, 254, 0.24);
}

.brand-mark {
  width: 58px;
  height: 58px;
  flex: 0 0 auto;
  padding: 6px;
  border: 1px solid rgba(219, 234, 254, 0.45);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(219, 234, 254, 0.86));
  box-shadow: 0 10px 24px rgb(2 6 23 / 18%);
}

.brand-name {
  color: #ffffff;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.1;
}

.brand-subtitle {
  margin-top: 3px;
  color: #bfdbfe;
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0;
}

.el-menu {
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: rgba(37, 99, 235, 0.32);
}

.el-menu-item.is-active {
  background: rgba(37, 99, 235, 0.48) !important;
}
</style>
