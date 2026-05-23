<template>
  <div class="max-w-md space-y-4">
    <h2 class="text-xl font-semibold text-slate-800">Container calculator</h2>
    <el-form label-position="top">
      <el-form-item label="Carton L (cm)"><el-input-number v-model="form.length_cm" :min="1" class="!w-full" /></el-form-item>
      <el-form-item label="Carton W (cm)"><el-input-number v-model="form.width_cm" :min="1" class="!w-full" /></el-form-item>
      <el-form-item label="Carton H (cm)"><el-input-number v-model="form.height_cm" :min="1" class="!w-full" /></el-form-item>
      <el-form-item label="Cartons"><el-input-number v-model="form.cartons" :min="1" class="!w-full" /></el-form-item>
      <el-button type="primary" @click="calc">Estimate</el-button>
    </el-form>
    <el-card v-if="result">
      <pre class="text-sm">{{ result }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { http } from '@/api/http'

const form = reactive({ length_cm: 50, width_cm: 40, height_cm: 30, cartons: 100 })
const result = ref<unknown>(null)

async function calc() {
  const { data } = await http.post('/container-calculator/estimate', form)
  result.value = data
}
</script>
