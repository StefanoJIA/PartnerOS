<template>
  <el-container class="h-screen">
    <el-aside width="220px" class="bg-slate-900 text-white">
      <div class="p-4 font-semibold tracking-tight">intelliOffice</div>
      <el-menu
        :default-active="$route.path"
        class="border-none bg-slate-900"
        text-color="#cbd5e1"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/">Dashboard</el-menu-item>
        <el-menu-item index="/system-health">System health</el-menu-item>
        <el-menu-item index="/portal-customer-bridge">Portal bridge UAT</el-menu-item>
        <el-menu-item index="/feedback-tickets">Feedback tickets</el-menu-item>
        <el-menu-item index="/lead-intelligence">A 域 · Lead Intelligence</el-menu-item>
        <el-menu-item index="/lead-intake">Lead Intake</el-menu-item>
        <el-menu-item index="/companies">Companies</el-menu-item>
        <el-menu-item index="/contacts">Contacts</el-menu-item>
        <el-menu-item index="/tasks">Tasks</el-menu-item>
        <el-menu-item index="/leads">Leads</el-menu-item>
        <el-menu-item index="/manufacturing-partners">Manufacturing partners</el-menu-item>
        <el-menu-item index="/products">Products</el-menu-item>
        <el-menu-item index="/rfqs">RFQs</el-menu-item>
        <el-menu-item index="/samples">Samples</el-menu-item>
        <el-menu-item index="/orders">Orders</el-menu-item>
        <el-menu-item index="/field-visits">Field visits</el-menu-item>
        <el-menu-item index="/market-intelligence">Market intel</el-menu-item>
        <el-menu-item index="/knowledge-base">Knowledge base</el-menu-item>
        <el-menu-item index="/ai-assistant">AI assistant</el-menu-item>
        <el-menu-item index="/ai-outputs">AI outputs</el-menu-item>
        <el-menu-item index="/container-calculator">Container calc</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="flex items-center justify-between border-b border-slate-200 bg-white">
        <span class="text-slate-600">{{ subtitle }}</span>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-500">{{ auth.email }}</span>
          <el-button size="small" @click="logout">Logout</el-button>
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

const subtitle = computed(() => (route.name as string) || '')

function logout() {
  auth.clear()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.el-menu-item.is-active {
  background: #1e293b !important;
}
</style>
