<template>
  <div class="mx-auto flex max-w-md flex-col gap-4 p-8">
    <h1 class="text-2xl font-semibold text-slate-800">intelliOffice PartnerOS</h1>
    <el-form @submit.prevent="onSubmit" label-position="top">
      <el-form-item label="邮箱">
        <el-input v-model="email" type="email" autocomplete="username" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="password" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" class="w-full">登录</el-button>
    </el-form>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p class="text-xs text-slate-500">本地默认账号：admin@example.com / admin123</p>
    <p class="text-xs text-slate-500">
      本地演示请使用 VITE_API_PROXY_TARGET=http://127.0.0.1:8014 启动前端，否则登录和 API 请求会失败。
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { formatApiError } from '@/api/errors'

const router = useRouter()
const auth = useAuthStore()
const email = ref('admin@example.com')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e: unknown) {
    error.value = formatApiError(
      e,
      '登录失败。请确认 backend 8014 已启动，并且前端 VITE_API_PROXY_TARGET 指向 http://127.0.0.1:8014。',
    )
  } finally {
    loading.value = false
  }
}
</script>
