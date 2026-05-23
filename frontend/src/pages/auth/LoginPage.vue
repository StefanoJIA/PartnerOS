<template>
  <div class="mx-auto flex max-w-md flex-col gap-4 p-8">
    <h1 class="text-2xl font-semibold text-slate-800">intelliOffice PartnerOS</h1>
    <el-form @submit.prevent="onSubmit" label-position="top">
      <el-form-item label="Email">
        <el-input v-model="email" type="email" autocomplete="username" />
      </el-form-item>
      <el-form-item label="Password">
        <el-input v-model="password" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" class="w-full">Sign in</el-button>
    </el-form>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p class="text-xs text-slate-500">Default seed: admin@example.com / admin123</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
    error.value = 'Login failed. Run backend + seed (see README).'
  } finally {
    loading.value = false
  }
}
</script>
