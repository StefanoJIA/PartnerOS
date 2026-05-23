<template>
  <div class="max-w-2xl space-y-4">
    <h2 class="text-xl font-semibold text-slate-800">Knowledge base (RAG)</h2>
    <p class="text-sm text-slate-600">Upload files via API <code>/api/files/upload</code> then ingest with <code>/api/knowledge/ingest</code>.</p>
    <el-input v-model="question" type="textarea" :rows="3" placeholder="Question" />
    <el-button type="primary" :loading="loading" @click="ask">Ask</el-button>
    <el-card v-if="answer">
      <template #header>Answer</template>
      <pre class="whitespace-pre-wrap text-sm">{{ answer }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { http } from '@/api/http'

const question = ref('')
const answer = ref('')
const loading = ref(false)

async function ask() {
  loading.value = true
  answer.value = ''
  try {
    const { data } = await http.post('/knowledge/query', { question: question.value, top_k: 5 })
    answer.value = data.answer
  } finally {
    loading.value = false
  }
}
</script>
