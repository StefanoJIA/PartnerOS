<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchOrders, type OrderSummary } from '@/api/orders'
import { ORDER_STATUS_LABELS, zhLabel } from '@/copy/zhCN'
import OperationalTracePanel from '@/components/dashboard/OperationalTracePanel.vue'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const items = ref<OrderSummary[]>([])
const statusFilter = ref('')

const SAFETY =
  '客户订单由已发送报价人工创建。创建订单不会启动生产、通知供应商、创建物流，也不会确认库存、认证或交期。'

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchOrders({ status: statusFilter.value || undefined })
    items.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '订单加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1>客户订单</h1>
    <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="SAFETY" class="mb" />

    <OperationalTracePanel
      title="Daily Queue / 订单交付回流"
      description="显示订单交付风险是否进入今日队列、谁在处理、是否阻塞、下一次跟进和内部处理备注。"
      category="order delivery"
      class="mb"
    />

    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 240px" @change="load">
        <el-option label="待客户确认" value="pending_customer_confirmation" />
        <el-option label="已确认" value="confirmed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <div v-if="loading" v-loading="true" style="min-height: 120px" />
    <el-table
      v-else
      :data="items"
      stripe
      @row-click="(row: OrderSummary) => router.push({ name: 'order-detail', params: { orderId: row.id } })"
    >
      <el-table-column prop="order_number" label="订单号" width="140" />
      <el-table-column prop="bill_to_company" label="公司" />
      <el-table-column label="状态" width="220">
        <template #default="{ row }">{{ zhLabel(ORDER_STATUS_LABELS, row.status) }}</template>
      </el-table-column>
      <el-table-column prop="grand_total" label="金额" width="140">
        <template #default="{ row }">{{ row.currency }} {{ row.grand_total }}</template>
      </el-table-column>
      <el-table-column prop="order_date" label="订单日期" width="120" />
      <el-table-column label="来源报价" width="140">
        <template #default="{ row }">
          <router-link
            class="link"
            :to="{ name: 'quote-detail', params: { id: row.source_quote_id } }"
            @click.stop
          >
            查看报价
          </router-link>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.link { color: var(--el-color-primary); }
</style>
