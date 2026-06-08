<template>
  <div class="space-y-6" v-loading="loading">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">行动看板</h2>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="router.push({ name: 'demo-walkthrough' })">Demo walkthrough</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </div>
    <p class="text-sm text-slate-600">
      今日应联系谁、处理哪些 RFQ、跟进哪些样品与订单——集中在一页。规则生成的建议可点击跳转。
    </p>

    <DailyOperationsPanel />

    <ProductOpportunitySummary />

    <EndOfDaySummaryPanel />

    <el-collapse class="border-0">
      <el-collapse-item title="更多行动看板（RFQ / 样品 / 订单 / 任务）" name="legacy">
        <div class="space-y-6 pt-2">
          <el-card shadow="never">
            <template #header>今日行动</template>
            <div class="grid gap-3 md:grid-cols-2">
              <div>
                <div class="mb-2 text-sm font-medium text-slate-700">今日到期任务</div>
                <ActionTaskList :items="data?.due_today_tasks" @go="goTask" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-slate-700">今日计划跟进（线索）</div>
                <ActionLeadList :items="data?.leads_follow_up_due_today" />
              </div>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header>逾期 / 风险</template>
            <div class="grid gap-4 md:grid-cols-3">
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">逾期任务</div>
                <ActionTaskList :items="data?.overdue_tasks" @go="goTask" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">跟进已过期线索</div>
                <ActionLeadList :items="data?.leads_needing_follow_up" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">订单节点延误</div>
                <ul v-if="data?.orders_delayed_milestones?.length" class="space-y-1 text-sm">
                  <li v-for="m in data.orders_delayed_milestones" :key="m.milestone_id">
                    <router-link class="text-blue-600 hover:underline" :to="{ name: 'order-detail', params: { orderId: m.order_id } }">
                      {{ m.order_number }} — {{ m.milestone_name }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
            </div>
          </el-card>

          <el-row :gutter="16">
            <el-col :xs="24" :md="12">
              <el-card shadow="never">
                <template #header>本周任务 &amp; 热门线索</template>
                <p class="mb-2 text-xs text-slate-500">本周到期</p>
                <ActionTaskList :items="data?.this_week_tasks" @go="goTask" />
                <p class="mb-2 mt-4 text-xs text-slate-500">高优先级线索</p>
                <ActionLeadList :items="data?.hot_leads" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card shadow="never">
                <template #header>线索动态</template>
                <p class="mb-2 text-xs text-slate-500">最近有互动</p>
                <ActionLeadList :items="data?.leads_recent_activity" />
                <p class="mb-2 mt-4 text-xs text-slate-500">等待下一步</p>
                <ActionLeadList :items="data?.leads_waiting_next_step" />
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>RFQ 关注</template>
                <p class="text-xs text-slate-500">等待伙伴报价</p>
                <RfqMini :items="data?.rfqs_waiting_partner_quote" />
                <p class="mt-3 text-xs text-slate-500">客户评审中</p>
                <RfqMini :items="data?.rfqs_customer_reviewing" />
                <p class="mt-3 text-xs text-slate-500">谈判中</p>
                <RfqMini :items="data?.rfqs_negotiating" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>样品关注</template>
                <p class="text-xs text-slate-500">已申请</p>
                <SampleMini :items="data?.samples_requested" />
                <p class="mt-3 text-xs text-slate-500">运输中</p>
                <SampleMini :items="data?.samples_shipped" />
                <p class="mt-3 text-xs text-slate-500">已签收待反馈</p>
                <SampleMini :items="data?.samples_delivered_no_feedback" />
                <p class="mt-3 text-xs text-slate-500">跟进到期</p>
                <SampleMini :items="data?.samples_follow_up_due" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>订单风险</template>
                <p class="text-xs text-slate-500">高风险订单</p>
                <ul v-if="data?.high_risk_orders?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.high_risk_orders" :key="o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                    <span class="text-slate-500">（{{ o.risk_level }}）</span>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
                <p class="mt-3 text-xs text-slate-500">交期临近但缺少 ETA / 海运记录</p>
                <ul v-if="data?.orders_eta_missing?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.orders_eta_missing" :key="'m-' + o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
                <p class="mt-3 text-xs text-slate-500">ETA 已过仍未交付</p>
                <ul v-if="data?.orders_eta_passed_not_delivered?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.orders_eta_passed_not_delivered" :key="'e-' + o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </el-card>
            </el-col>
          </el-row>

          <el-card shadow="never">
            <template #header>推荐下一步（规则生成）</template>
            <ul v-if="data?.recommended_actions?.length" class="space-y-2">
              <li v-for="a in data.recommended_actions" :key="a.id" class="rounded border border-slate-100 bg-white p-3 text-sm">
                <div class="font-medium text-slate-800">{{ a.title }}</div>
                <div class="text-slate-600">{{ a.message }}</div>
                <el-button class="mt-2" size="small" type="primary" link @click="followRec(a)">前往处理</el-button>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">暂无新建议</p>
          </el-card>

          <el-card shadow="never">
            <template #header>最近 AI 产出</template>
            <ul v-if="data?.recent_ai_outputs?.length" class="text-sm space-y-1">
              <li v-for="x in data.recent_ai_outputs" :key="x.id">
                <router-link to="/ai-outputs" class="text-blue-600 hover:underline">{{ x.task_type }}</router-link>
                <span class="text-slate-400"> · {{ x.status }}</span>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">暂无</p>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDashboardActions, type DashboardActions, type RecommendedAction } from '@/api/dashboard'
import ActionTaskList from './dashboard/ActionTaskList.vue'
import ActionLeadList from './dashboard/ActionLeadList.vue'
import RfqMini from './dashboard/RfqMini.vue'
import SampleMini from './dashboard/SampleMini.vue'
import DailyOperationsPanel from '@/components/dashboard/DailyOperationsPanel.vue'
import ProductOpportunitySummary from '@/components/dashboard/ProductOpportunitySummary.vue'
import EndOfDaySummaryPanel from '@/components/dashboard/EndOfDaySummaryPanel.vue'

const router = useRouter()
const loading = ref(false)
const data = ref<DashboardActions | null>(null)

function goTask(id: string) {
  router.push({ path: '/tasks', query: { focus: id } })
}

function followRec(a: RecommendedAction) {
  const id = a.object_id
  const t = a.object_type
  if (t === 'lead') router.push({ name: 'lead-detail', params: { leadId: id } })
  else if (t === 'rfq') router.push({ name: 'rfq-detail', params: { rfqId: id } })
  else if (t === 'sample') router.push({ name: 'sample-detail', params: { sampleId: id } })
  else if (t === 'order') router.push({ name: 'order-detail', params: { orderId: id } })
  else if (t === 'task') router.push({ path: '/tasks', query: { focus: id } })
  else router.push(a.path)
}

async function load() {
  loading.value = true
  try {
    data.value = await fetchDashboardActions()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
