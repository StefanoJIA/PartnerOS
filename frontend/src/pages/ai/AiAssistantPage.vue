<template>
  <div class="max-w-3xl space-y-4">
    <h2 class="text-xl font-semibold text-slate-800">AI assistant</h2>
    <el-radio-group v-model="mode">
      <el-radio-button label="linkedin">LinkedIn note</el-radio-button>
      <el-radio-button label="email">Email</el-radio-button>
      <el-radio-button label="follow">Follow-up</el-radio-button>
      <el-radio-button label="profile">Customer profile</el-radio-button>
    </el-radio-group>
    <el-input v-model="ctx" type="textarea" :rows="6" placeholder="Paste context (company, contact, interests...)" />
    <el-button type="primary" :loading="loading" @click="run">Generate</el-button>
    <el-card v-if="out">
      <template #header>Output</template>
      <pre class="whitespace-pre-wrap text-sm text-slate-800">{{ out }}</pre>
      <el-button class="mt-2" size="small" @click="copy">Copy</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { http } from '@/api/http'
import { ElMessage } from 'element-plus'

const mode = ref('linkedin')
const ctx = ref('')
const out = ref('')
const loading = ref(false)

async function run() {
  loading.value = true
  out.value = ''
  try {
    const body = { context: { notes: ctx.value } }
    let path = '/ai/linkedin-note'
    if (mode.value === 'email') path = '/ai/email'
    if (mode.value === 'follow') path = '/ai/follow-up'
    if (mode.value === 'profile') path = '/ai/customer-profile'
    const { data } = await http.post(path, body)
    out.value = data.output_text || ''
  } finally {
    loading.value = false
  }
}

async function copy() {
  await navigator.clipboard.writeText(out.value)
  ElMessage.success('Copied')
}
</script>
