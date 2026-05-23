<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'rfqs' })">← RFQ 列表</el-button>

    <template v-if="ws">
      <el-card shadow="never">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-800">{{ ws.rfq.rfq_number }}</h2>
            <p class="mt-1 text-sm text-slate-600">状态：{{ ws.rfq.status }} · 负责人：{{ ws.owner_display || ws.rfq.owner_user_id || '—' }}</p>
            <p class="mt-2 whitespace-pre-wrap text-sm text-slate-800">{{ ws.rfq.customer_requirement || '—' }}</p>
            <p class="mt-2 text-sm text-slate-600">
              数量：{{ ws.rfq.quantity ?? '—' }} · 目标价：{{ ws.rfq.target_price ?? '—' }} · 目标交期：{{ ws.rfq.target_delivery_date || '—' }}
            </p>
            <p class="text-sm text-slate-600">认证要求：{{ ws.rfq.required_certifications || '—' }}</p>
            <p class="text-sm text-slate-600">包装：{{ ws.rfq.packaging_requirement || '—' }}</p>
            <p class="text-sm text-slate-600">物流：{{ ws.rfq.shipping_requirement || '—' }}</p>
            <p class="mt-1 text-xs text-slate-500">创建于 {{ ws.rfq.created_at }} · 更新 {{ ws.rfq.updated_at }}</p>
          </div>
          <div class="text-right text-sm text-slate-600 space-y-1">
            <div v-if="ws.company">公司：{{ ws.company.company_name }}</div>
            <div v-if="ws.contact">联系人：{{ ws.contact.first_name }} {{ ws.contact.last_name }}</div>
            <div v-if="ws.lead">线索：{{ ws.lead.lead_name }}</div>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <el-button v-if="ws.company" size="small" @click="$router.push({ name: 'company-detail', params: { companyId: ws.company.id } })">
            打开公司
          </el-button>
          <el-button v-if="ws.contact" size="small" @click="$router.push({ name: 'contact-detail', params: { contactId: ws.contact.id } })">
            打开联系人
          </el-button>
          <el-button v-if="ws.lead" size="small" @click="$router.push({ name: 'lead-detail', params: { leadId: ws.lead.id } })">打开线索</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>状态管线</template>
        <div class="flex flex-wrap gap-2">
          <el-button
            v-for="st in RFQ_PIPELINE"
            :key="st"
            size="small"
            :type="ws.rfq.status === st ? 'primary' : 'default'"
            @click="setStatus(st)"
          >
            {{ st }}
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>快捷动作（MVP）</template>
        <div class="flex flex-wrap gap-2">
          <el-button size="small" @click="openItemDialog()">添加行项目</el-button>
          <el-button size="small" @click="openCandDialog()">添加候选伙伴</el-button>
          <el-button size="small" @click="scrollTo('candidates')">索要伙伴报价</el-button>
          <el-button size="small" type="primary" @click="openQuoteDialog()">添加伙伴报价</el-button>
          <el-button size="small" @click="scrollTo('comparison')">生成/查看比价</el-button>
          <el-button size="small" @click="scrollTo('ai-panel')">客户报价邮件（AI）</el-button>
          <el-button size="small" @click="scrollTo('ai-panel')">跟进邮件（AI）</el-button>
          <el-button size="small" @click="openSampleDialog()">转为样品</el-button>
          <el-button size="small" type="primary" @click="openOrderDialog()">转为订单</el-button>
          <el-button size="small" @click="scrollTo('task-panel')">创建任务</el-button>
          <el-button size="small" @click="scrollTo('interaction-panel')">记录互动</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>RFQ 行项目</template>
        <el-table :data="ws.rfq_items" size="small" stripe>
          <template #empty>
            <el-empty description="暂无行项目" />
          </template>
          <el-table-column label="产品">
            <template #default="{ row }">
              <router-link
                v-if="row.product"
                class="text-blue-600"
                :to="{ name: 'product-detail', params: { productId: row.product.id } }"
              >
                {{ row.product.product_name }}
              </router-link>
              <span v-else class="text-slate-400">—</span>
            </template>
          </el-table-column>
          <el-table-column label="品类" width="120">
            <template #default="{ row }">{{ row.product?.product_category || '—' }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="spec_notes" label="规格/备注" min-width="120" />
          <el-table-column prop="target_price" label="目标价" width="90" />
          <el-table-column prop="required_certifications" label="认证" min-width="100" show-overflow-tooltip />
          <el-table-column prop="packaging_requirement" label="包装" min-width="100" show-overflow-tooltip />
          <el-table-column prop="shipping_requirement" label="物流" min-width="100" show-overflow-tooltip />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openItemDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removeItem(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card id="candidates" shadow="never">
        <template #header>候选制造伙伴</template>
        <el-table :data="ws.partner_candidates_with_partner_detail" size="small" stripe>
          <template #empty>
            <el-empty description="暂无候选制造伙伴" />
          </template>
          <el-table-column label="伙伴">
            <template #default="{ row }">
              <router-link class="text-blue-600" :to="{ name: 'partner-detail', params: { partnerId: row.partner.id } }">
                {{ row.partner.partner_name }}
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="100">
            <template #default="{ row }">{{ row.partner?.partner_type }}</template>
          </el-table-column>
          <el-table-column prop="product_fit" label="匹配" width="90" />
          <el-table-column prop="capability_level" label="能力" width="90" />
          <el-table-column prop="partner_moq" label="MOQ" width="70" />
          <el-table-column prop="lead_time_days" label="交期天" width="80" />
          <el-table-column prop="partner_price_range" label="价格带" min-width="100" />
          <el-table-column label="样品" width="70">
            <template #default="{ row }">{{ row.sample_available === true ? '是' : row.sample_available === false ? '否' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="certification_status" label="认证" min-width="90" />
          <el-table-column prop="partner_status" label="状态" width="120" />
          <el-table-column prop="quote_requested_at" label="询价时间" width="160" />
          <el-table-column prop="quote_received_at" label="回价时间" width="160" />
          <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openCandDialog(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="markQuoteRequested(row.id)">已询价</el-button>
              <el-button link type="primary" size="small" @click="markQuoteReceived(row.id)">已回价</el-button>
              <el-button link type="danger" size="small" @click="removeCand(row.id)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>伙伴报价</template>
        <el-table :data="ws.quotations" size="small" stripe>
          <template #empty>
            <el-empty description="暂无伙伴报价" />
          </template>
          <el-table-column label="制造伙伴" min-width="140">
            <template #default="{ row }">
              <router-link
                v-if="row.manufacturing_partner_id"
                class="text-blue-600"
                :to="{ name: 'partner-detail', params: { partnerId: row.manufacturing_partner_id } }"
              >
                {{ row.partner?.partner_name || row.manufacturing_partner_id }}
              </router-link>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column label="产品" min-width="120">
            <template #default="{ row }">
              <router-link
                v-if="row.product_id"
                class="text-blue-600"
                :to="{ name: 'product-detail', params: { productId: row.product_id } }"
              >
                {{ row.product?.product_name || row.product_id }}
              </router-link>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="70" />
          <el-table-column prop="unit_price" label="单价" width="80" />
          <el-table-column prop="currency" label="币别" width="70" />
          <el-table-column prop="incoterm" label="条款" width="80" />
          <el-table-column prop="moq" label="MOQ" width="60" />
          <el-table-column prop="lead_time" label="交期" width="90" />
          <el-table-column prop="sample_cost" label="样品费" width="80" />
          <el-table-column prop="tooling_cost" label="模具" width="80" />
          <el-table-column prop="packaging_cost" label="包装" width="80" />
          <el-table-column prop="estimated_shipping_cost" label="运费估" width="80" />
          <el-table-column prop="landed_cost" label="到岸" width="80" />
          <el-table-column prop="target_margin" label="目标毛利" width="90" />
          <el-table-column prop="valid_until" label="有效至" width="110" />
          <el-table-column prop="notes" label="备注" min-width="100" show-overflow-tooltip />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openQuoteDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removeQuote(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card id="comparison" shadow="never">
        <template #header>报价对比（规则）</template>
        <div v-if="ws.quotation_comparison" class="space-y-2 text-sm text-slate-700">
          <div>最优单价：{{ fmtPick(ws.quotation_comparison.best_price_option) }}</div>
          <div>最优到岸：{{ fmtPick(ws.quotation_comparison.best_landed_cost_option) }}</div>
          <div>最短交期：{{ fmtPick(ws.quotation_comparison.best_lead_time_option) }}</div>
          <div>MOQ 灵活：{{ fmtPick(ws.quotation_comparison.best_moq_option) }}</div>
          <div>样品：{{ fmtPick(ws.quotation_comparison.best_sample_option) }}</div>
          <div>认证信号：{{ fmtPick(ws.quotation_comparison.best_certification_option) }}</div>
          <div>项目适配度：{{ fmtPick(ws.quotation_comparison.best_project_fit_option) }}</div>
          <div>目标毛利：{{ fmtPick(ws.quotation_comparison.best_margin_option) }}</div>
          <div class="font-medium">综合：{{ fmtPick(ws.quotation_comparison.best_overall_option) }}</div>
          <ul v-if="ws.quotation_comparison.risk_notes?.length" class="mt-2 list-disc pl-5 text-amber-800">
            <li v-for="(n, i) in ws.quotation_comparison.risk_notes" :key="i">{{ n }}</li>
          </ul>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>关联样品 / 订单</template>
        <div class="grid gap-4 md:grid-cols-2 text-sm">
          <div>
            <div class="mb-1 font-medium text-slate-700">样品</div>
            <ul class="space-y-1">
              <li v-for="s in ws.related_samples" :key="s.id">
                <router-link class="text-blue-600" :to="{ name: 'sample-detail', params: { sampleId: s.id } }">{{
                  s.sample_request_number
                }}</router-link>
                <span class="text-slate-400"> — {{ s.sample_status }}</span>
              </li>
            </ul>
            <p v-if="!ws.related_samples?.length" class="text-slate-500">暂无</p>
          </div>
          <div>
            <div class="mb-1 font-medium text-slate-700">订单</div>
            <ul class="space-y-1">
              <li v-for="o in ws.related_orders" :key="o.id">
                <router-link class="text-blue-600" :to="{ name: 'order-detail', params: { orderId: o.id } }">{{ o.order_number }}</router-link>
                <span class="text-slate-400"> — {{ o.production_status }}</span>
              </li>
            </ul>
            <p v-if="!ws.related_orders?.length" class="text-slate-500">暂无</p>
          </div>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>活动摘要</template>
        <p v-if="!activityEntries.length" class="text-sm text-slate-500">暂无聚合数据</p>
        <div v-else class="flex flex-wrap gap-2 text-xs">
          <el-tag v-for="[action, count] in activityEntries" :key="action" size="small" type="info">{{ action }}: {{ count }}</el-tag>
        </div>
      </el-card>

      <div id="ai-panel">
        <ObjectAiActionsPanel object-type="rfq" :object-id="rfqId" variant="rfq" :ai-context="aiContext" />
      </div>
      <div id="interaction-panel" class="mt-4">
        <ObjectInteractionsPanel object-type="rfq" :object-id="rfqId" @task-spawned="reload" />
      </div>
      <div id="task-panel" class="mt-4">
        <ObjectTasksPanel object-type="rfq" :object-id="rfqId" />
      </div>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <ObjectNotesPanel object-type="rfq" :object-id="rfqId" />
        <ObjectTagsPanel object-type="rfq" :object-id="rfqId" />
        <ObjectFilesPanel object-type="rfq" :object-id="rfqId" />
        <div class="lg:col-span-2">
          <ObjectActivityLogPanel object-type="rfq" :object-id="rfqId" />
        </div>
      </div>
    </template>

    <!-- Item dialog -->
    <el-dialog v-model="itemDlg" :title="itemForm.id ? '编辑行项目' : '添加行项目'" width="520">
      <el-form label-position="top">
        <el-form-item label="产品">
          <el-select v-model="itemForm.product_id" filterable clearable placeholder="选择产品" class="w-full">
            <el-option v-for="p in productOptions" :key="p.id" :label="p.product_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="itemForm.quantity" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="规格/备注"><el-input v-model="itemForm.spec_notes" type="textarea" /></el-form-item>
        <el-form-item label="目标价"><el-input v-model="itemForm.target_price" /></el-form-item>
        <el-form-item label="认证"><el-input v-model="itemForm.required_certifications" /></el-form-item>
        <el-form-item label="包装"><el-input v-model="itemForm.packaging_requirement" /></el-form-item>
        <el-form-item label="物流"><el-input v-model="itemForm.shipping_requirement" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDlg = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <!-- Candidate dialog -->
    <el-dialog v-model="candDlg" :title="candForm.id ? '编辑候选' : '添加候选伙伴'" width="560">
      <el-form label-position="top">
        <el-form-item label="制造伙伴">
          <el-select v-model="candForm.partner_id" filterable :disabled="!!candForm.id" placeholder="伙伴" class="w-full">
            <el-option v-for="p in partnerOptions" :key="p.id" :label="p.partner_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="candForm.partner_status" class="w-full" filterable>
            <el-option v-for="s in RFQ_CANDIDATE_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="手动优选"><el-switch v-model="candForm.is_preferred" /></el-form-item>
        <el-form-item label="能力等级"><el-input v-model="candForm.capability_level" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="candForm.partner_moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="candForm.lead_time_days" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="价格带"><el-input v-model="candForm.partner_price_range" /></el-form-item>
        <el-form-item label="样品可得">
          <el-select v-model="candForm.sample_available" clearable placeholder="未填" class="w-full">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证状态"><el-input v-model="candForm.certification_status" /></el-form-item>
        <el-form-item label="产品匹配"><el-input v-model="candForm.product_fit" placeholder="high / medium / low" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="candForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="candDlg = false">取消</el-button>
        <el-button type="primary" @click="saveCand">保存</el-button>
      </template>
    </el-dialog>

    <!-- Quotation dialog -->
    <el-dialog v-model="quoteDlg" :title="quoteForm.id ? '编辑报价' : '添加报价'" width="600">
      <el-form label-position="top">
        <el-form-item label="制造伙伴">
          <el-select v-model="quoteForm.manufacturing_partner_id" filterable class="w-full">
            <el-option v-for="p in partnerOptions" :key="p.id" :label="p.partner_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品">
          <el-select v-model="quoteForm.product_id" filterable clearable class="w-full">
            <el-option v-for="p in productOptions" :key="p.id" :label="p.product_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="quoteForm.quantity" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="单价"><el-input v-model="quoteForm.unit_price" /></el-form-item>
        <el-form-item label="币别"><el-input v-model="quoteForm.currency" placeholder="USD" /></el-form-item>
        <el-form-item label="条款"><el-input v-model="quoteForm.incoterm" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="quoteForm.moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(文本)"><el-input v-model="quoteForm.lead_time" placeholder="e.g. 30 days" /></el-form-item>
        <el-form-item label="样品费"><el-input v-model="quoteForm.sample_cost" /></el-form-item>
        <el-form-item label="模具费"><el-input v-model="quoteForm.tooling_cost" /></el-form-item>
        <el-form-item label="包装费"><el-input v-model="quoteForm.packaging_cost" /></el-form-item>
        <el-form-item label="运费估"><el-input v-model="quoteForm.estimated_shipping_cost" /></el-form-item>
        <el-form-item label="到岸成本"><el-input v-model="quoteForm.landed_cost" /></el-form-item>
        <el-form-item label="目标毛利"><el-input v-model="quoteForm.target_margin" /></el-form-item>
        <el-form-item label="有效至"><el-input v-model="quoteForm.valid_until" placeholder="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="quoteForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quoteDlg = false">取消</el-button>
        <el-button type="primary" @click="saveQuote">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sampleDlg" title="转为样品" width="480">
      <el-form label-position="top">
        <el-form-item label="RFQ 行项目">
          <el-select v-model="sampleBody.rfq_item_id" class="w-full">
            <el-option v-for="it in ws?.rfq_items || []" :key="it.id" :label="lineLabel(it)" :value="it.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="制造伙伴">
          <el-select v-model="sampleBody.manufacturing_partner_id" filterable class="w-full">
            <el-option v-for="p in partnerOptions" :key="p.id" :label="p.partner_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="sampleBody.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sampleDlg = false">取消</el-button>
        <el-button type="primary" @click="doConvertSample">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="orderDlg" title="转为订单" width="520">
      <el-form label-position="top">
        <el-form-item label="使用已有报价（可选）">
          <el-select v-model="orderBody.quote_id" clearable class="w-full" placeholder="不选则用行项目">
            <el-option v-for="q in ws?.quotations || []" :key="q.id" :label="quoteLabel(q)" :value="q.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!orderBody.quote_id" label="RFQ 行项目">
          <el-select v-model="orderBody.rfq_item_id" clearable class="w-full">
            <el-option v-for="it in ws?.rfq_items || []" :key="it.id" :label="lineLabel(it)" :value="it.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="制造伙伴">
          <el-select v-model="orderBody.manufacturing_partner_id" filterable class="w-full">
            <el-option v-for="p in partnerOptions" :key="p.id" :label="p.partner_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成生产里程碑"><el-switch v-model="orderBody.generate_milestones" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="orderBody.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="orderDlg = false">取消</el-button>
        <el-button type="primary" @click="doConvertOrder">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'
import { RFQ_CANDIDATE_STATUSES, RFQ_STATUSES } from '@/constants/statusEnums'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import { ElMessage, ElMessageBox } from 'element-plus'

interface RfqCore {
  id: string
  rfq_number: string
  status: string
  owner_user_id?: string | null
  customer_requirement?: string | null
  quantity?: number | null
  target_price?: string | number | null
  target_delivery_date?: string | null
  required_certifications?: string | null
  packaging_requirement?: string | null
  shipping_requirement?: string | null
  created_at: string
  updated_at: string
}

interface ProductMini {
  id: string
  product_name: string
  product_category?: string | null
}

interface RfqItemRow {
  id: string
  product_id?: string | null
  product?: ProductMini | null
  quantity?: number | null
  spec_notes?: string | null
  target_price?: number | string | null
  required_certifications?: string | null
  packaging_requirement?: string | null
  shipping_requirement?: string | null
}

interface PartnerMini {
  id: string
  partner_name: string
  partner_type: string
}

interface CandRow {
  id: string
  partner_id: string
  partner_status?: string | null
  is_preferred?: boolean
  capability_level?: string | null
  partner_moq?: number | null
  lead_time_days?: number | null
  partner_price_range?: string | null
  sample_available?: boolean | null
  certification_status?: string | null
  product_fit?: string | null
  quote_requested_at?: string | null
  quote_received_at?: string | null
  notes?: string | null
  partner: PartnerMini
}

interface QuoteRow {
  id: string
  manufacturing_partner_id?: string | null
  product_id?: string | null
  quantity?: number | null
  unit_price?: number | string | null
  currency?: string | null
  incoterm?: string | null
  moq?: number | null
  lead_time?: string | null
  sample_cost?: number | string | null
  tooling_cost?: number | string | null
  packaging_cost?: number | string | null
  estimated_shipping_cost?: number | string | null
  landed_cost?: number | string | null
  target_margin?: number | string | null
  valid_until?: string | null
  notes?: string | null
  partner?: PartnerMini | null
  product?: ProductMini | null
}

interface ComparisonPick {
  quotation_id?: string | null
  rationale?: string
  missing_data?: boolean
}

interface QuotationComparison {
  best_price_option?: ComparisonPick | null
  best_landed_cost_option?: ComparisonPick | null
  best_lead_time_option?: ComparisonPick | null
  best_moq_option?: ComparisonPick | null
  best_sample_option?: ComparisonPick | null
  best_certification_option?: ComparisonPick | null
  best_project_fit_option?: ComparisonPick | null
  best_margin_option?: ComparisonPick | null
  best_overall_option?: ComparisonPick | null
  risk_notes?: string[]
}

interface SampleBrief {
  id: string
  sample_request_number: string
  sample_status: string
}

interface OrderBrief {
  id: string
  order_number: string
  production_status?: string | null
}

interface RfqWorkspace {
  rfq: RfqCore
  company?: { id: string; company_name: string }
  contact?: { id: string; first_name: string; last_name: string }
  lead?: { id: string; lead_name: string }
  owner_display?: string | null
  rfq_items: RfqItemRow[]
  partner_candidates_with_partner_detail: CandRow[]
  quotations: QuoteRow[]
  quotation_comparison: QuotationComparison
  related_samples: SampleBrief[]
  related_orders: OrderBrief[]
  activity_summary?: { by_action: Record<string, number> }
}

const RFQ_PIPELINE = RFQ_STATUSES
const route = useRoute()
const rfqId = computed(() => route.params.rfqId as string)

const loading = ref(true)
const ws = ref<RfqWorkspace | null>(null)

const activityEntries = computed(() => {
  const m = ws.value?.activity_summary?.by_action
  if (!m) return [] as [string, number][]
  return Object.entries(m).sort((a, b) => b[1] - a[1])
})

const productOptions = ref<{ id: string; product_name: string }[]>([])
const partnerOptions = ref<{ id: string; partner_name: string }[]>([])

const itemDlg = ref(false)
const itemForm = reactive({
  id: '' as string,
  product_id: undefined as string | undefined,
  quantity: undefined as number | undefined,
  spec_notes: '',
  target_price: '',
  required_certifications: '',
  packaging_requirement: '',
  shipping_requirement: '',
})

const candDlg = ref(false)
const candForm = reactive({
  id: '' as string,
  partner_id: '' as string,
  partner_status: 'Candidate',
  is_preferred: false,
  capability_level: '',
  partner_moq: undefined as number | undefined,
  lead_time_days: undefined as number | undefined,
  partner_price_range: '',
  sample_available: undefined as boolean | undefined,
  certification_status: '',
  product_fit: '',
  notes: '',
})

const quoteDlg = ref(false)
const quoteForm = reactive({
  id: '' as string,
  manufacturing_partner_id: '' as string,
  product_id: undefined as string | undefined,
  quantity: undefined as number | undefined,
  unit_price: '',
  currency: 'USD',
  incoterm: '',
  moq: undefined as number | undefined,
  lead_time: '',
  sample_cost: '',
  tooling_cost: '',
  packaging_cost: '',
  estimated_shipping_cost: '',
  landed_cost: '',
  target_margin: '',
  valid_until: '',
  notes: '',
})

const sampleDlg = ref(false)
const sampleBody = reactive({
  rfq_item_id: '',
  manufacturing_partner_id: '',
  notes: '',
})

const orderDlg = ref(false)
const orderBody = reactive({
  quote_id: undefined as string | undefined,
  rfq_item_id: undefined as string | undefined,
  manufacturing_partner_id: '',
  generate_milestones: false,
  notes: '',
})

const aiContext = computed(() => {
  const w = ws.value
  if (!w) return {}
  const rfq = w.rfq
  return {
    rfq_number: rfq.rfq_number,
    status: rfq.status,
    customer_requirement: rfq.customer_requirement,
    required_certifications: rfq.required_certifications,
    target_delivery_date: rfq.target_delivery_date,
    rfq_items_json: JSON.stringify(w.rfq_items ?? []),
    quotations_json: JSON.stringify(w.quotations ?? []),
    partner_candidates_json: JSON.stringify(w.partner_candidates_with_partner_detail ?? []),
    quotation_comparison_json: JSON.stringify(w.quotation_comparison ?? {}),
  }
})

function fmtPick(p: { quotation_id?: string | null; rationale?: string; missing_data?: boolean } | null | undefined) {
  if (!p) return '—'
  const id = p.quotation_id || '—'
  const miss = p.missing_data ? '（数据不足）' : ''
  return `${id} ${p.rationale || ''}${miss}`
}

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function lineLabel(it: RfqItemRow) {
  return it.product?.product_name || it.spec_notes || it.id
}

function quoteLabel(q: QuoteRow) {
  return `${q.partner?.partner_name || q.id} @ ${q.unit_price ?? '—'}`
}

async function loadMeta() {
  const [pr, pa] = await Promise.all([
    http.get('/products', { params: { page: 1, limit: 200 } }),
    http.get('/manufacturing-partners', { params: { page: 1, limit: 200 } }),
  ])
  productOptions.value = pr.data.items
  partnerOptions.value = pa.data.items
}

async function reload() {
  loading.value = true
  try {
    const { data } = await http.get<RfqWorkspace>(`/rfqs/${rfqId.value}/workspace`)
    ws.value = data
  } finally {
    loading.value = false
  }
}

async function setStatus(st: string) {
  await http.post(`/rfqs/${rfqId.value}/status`, { status: st })
  ElMessage.success('状态已更新')
  reload()
}

function openItemDialog(row?: RfqItemRow) {
  if (row) {
    itemForm.id = row.id
    itemForm.product_id = row.product_id || row.product?.id
    itemForm.quantity = row.quantity ?? undefined
    itemForm.spec_notes = row.spec_notes || ''
    itemForm.target_price = row.target_price != null ? String(row.target_price) : ''
    itemForm.required_certifications = row.required_certifications || ''
    itemForm.packaging_requirement = row.packaging_requirement || ''
    itemForm.shipping_requirement = row.shipping_requirement || ''
  } else {
    itemForm.id = ''
    itemForm.product_id = undefined
    itemForm.quantity = undefined
    itemForm.spec_notes = ''
    itemForm.target_price = ''
    itemForm.required_certifications = ''
    itemForm.packaging_requirement = ''
    itemForm.shipping_requirement = ''
  }
  itemDlg.value = true
}

async function saveItem() {
  const body: Record<string, unknown> = {
    product_id: itemForm.product_id || null,
    quantity: itemForm.quantity ?? null,
    spec_notes: itemForm.spec_notes || null,
    target_price: itemForm.target_price ? Number(itemForm.target_price) : null,
    required_certifications: itemForm.required_certifications || null,
    packaging_requirement: itemForm.packaging_requirement || null,
    shipping_requirement: itemForm.shipping_requirement || null,
  }
  if (itemForm.id) {
    await http.put(`/rfqs/${rfqId.value}/items/${itemForm.id}`, body)
  } else {
    await http.post(`/rfqs/${rfqId.value}/items`, body)
  }
  ElMessage.success('已保存')
  itemDlg.value = false
  reload()
}

async function removeItem(row: RfqItemRow) {
  await ElMessageBox.confirm('删除此行项目？', '确认')
  await http.delete(`/rfqs/${rfqId.value}/items/${row.id}`)
  ElMessage.success('已删除')
  reload()
}

function openCandDialog(row?: CandRow) {
  if (row) {
    candForm.id = row.id
    candForm.partner_id = row.partner_id
    candForm.partner_status = row.partner_status || 'Candidate'
    candForm.is_preferred = !!row.is_preferred
    candForm.capability_level = row.capability_level || ''
    candForm.partner_moq = row.partner_moq ?? undefined
    candForm.lead_time_days = row.lead_time_days ?? undefined
    candForm.partner_price_range = row.partner_price_range || ''
    candForm.sample_available = row.sample_available ?? undefined
    candForm.certification_status = row.certification_status || ''
    candForm.product_fit = row.product_fit || ''
    candForm.notes = row.notes || ''
  } else {
    candForm.id = ''
    candForm.partner_id = ''
    candForm.partner_status = 'Candidate'
    candForm.is_preferred = false
    candForm.capability_level = ''
    candForm.partner_moq = undefined
    candForm.lead_time_days = undefined
    candForm.partner_price_range = ''
    candForm.sample_available = undefined
    candForm.certification_status = ''
    candForm.product_fit = ''
    candForm.notes = ''
  }
  candDlg.value = true
}

async function saveCand() {
  if (!candForm.partner_id) {
    ElMessage.error('请选择伙伴')
    return
  }
  const body = {
    partner_id: candForm.partner_id,
    partner_status: candForm.partner_status || null,
    is_preferred: candForm.is_preferred,
    capability_level: candForm.capability_level || null,
    partner_moq: candForm.partner_moq ?? null,
    lead_time_days: candForm.lead_time_days ?? null,
    partner_price_range: candForm.partner_price_range || null,
    sample_available: candForm.sample_available ?? null,
    certification_status: candForm.certification_status || null,
    product_fit: candForm.product_fit || null,
    notes: candForm.notes || null,
  }
  if (candForm.id) {
    await http.put(`/rfqs/${rfqId.value}/partner-candidates/${candForm.id}`, body)
  } else {
    await http.post(`/rfqs/${rfqId.value}/partner-candidates`, body)
  }
  ElMessage.success('已保存')
  candDlg.value = false
  reload()
}

async function markQuoteRequested(id: string) {
  await http.post(`/rfqs/${rfqId.value}/partner-candidates/${id}/quote-requested`)
  ElMessage.success('已标记询价')
  reload()
}

async function markQuoteReceived(id: string) {
  await http.post(`/rfqs/${rfqId.value}/partner-candidates/${id}/quote-received`)
  ElMessage.success('已标记回价')
  reload()
}

async function removeCand(id: string) {
  await ElMessageBox.confirm('移除该候选？', '确认')
  await http.delete(`/rfqs/${rfqId.value}/partner-candidates/${id}`)
  ElMessage.success('已移除')
  reload()
}

function openQuoteDialog(row?: QuoteRow) {
  if (row) {
    quoteForm.id = row.id
    quoteForm.manufacturing_partner_id = row.manufacturing_partner_id || ''
    quoteForm.product_id = row.product_id || undefined
    quoteForm.quantity = row.quantity ?? undefined
    quoteForm.unit_price = row.unit_price != null ? String(row.unit_price) : ''
    quoteForm.currency = row.currency || 'USD'
    quoteForm.incoterm = row.incoterm || ''
    quoteForm.moq = row.moq ?? undefined
    quoteForm.lead_time = row.lead_time || ''
    quoteForm.sample_cost = row.sample_cost != null ? String(row.sample_cost) : ''
    quoteForm.tooling_cost = row.tooling_cost != null ? String(row.tooling_cost) : ''
    quoteForm.packaging_cost = row.packaging_cost != null ? String(row.packaging_cost) : ''
    quoteForm.estimated_shipping_cost = row.estimated_shipping_cost != null ? String(row.estimated_shipping_cost) : ''
    quoteForm.landed_cost = row.landed_cost != null ? String(row.landed_cost) : ''
    quoteForm.target_margin = row.target_margin != null ? String(row.target_margin) : ''
    quoteForm.valid_until = row.valid_until || ''
    quoteForm.notes = row.notes || ''
  } else {
    quoteForm.id = ''
    quoteForm.manufacturing_partner_id = ''
    quoteForm.product_id = undefined
    quoteForm.quantity = undefined
    quoteForm.unit_price = ''
    quoteForm.currency = 'USD'
    quoteForm.incoterm = ''
    quoteForm.moq = undefined
    quoteForm.lead_time = ''
    quoteForm.sample_cost = ''
    quoteForm.tooling_cost = ''
    quoteForm.packaging_cost = ''
    quoteForm.estimated_shipping_cost = ''
    quoteForm.landed_cost = ''
    quoteForm.target_margin = ''
    quoteForm.valid_until = ''
    quoteForm.notes = ''
  }
  quoteDlg.value = true
}

function numOrNull(s: string) {
  if (!s) return null
  const n = Number(s)
  return Number.isFinite(n) ? n : null
}

async function saveQuote() {
  if (!quoteForm.manufacturing_partner_id) {
    ElMessage.error('请选择制造伙伴')
    return
  }
  const body: Record<string, unknown> = {
    manufacturing_partner_id: quoteForm.manufacturing_partner_id,
    product_id: quoteForm.product_id || null,
    quantity: quoteForm.quantity ?? null,
    unit_price: numOrNull(quoteForm.unit_price),
    currency: quoteForm.currency || 'USD',
    incoterm: quoteForm.incoterm || null,
    moq: quoteForm.moq ?? null,
    lead_time: quoteForm.lead_time || null,
    sample_cost: numOrNull(quoteForm.sample_cost),
    tooling_cost: numOrNull(quoteForm.tooling_cost),
    packaging_cost: numOrNull(quoteForm.packaging_cost),
    estimated_shipping_cost: numOrNull(quoteForm.estimated_shipping_cost),
    landed_cost: numOrNull(quoteForm.landed_cost),
    target_margin: numOrNull(quoteForm.target_margin),
    valid_until: quoteForm.valid_until || null,
    notes: quoteForm.notes || null,
  }
  if (quoteForm.id) {
    await http.put(`/quotations/${quoteForm.id}`, body)
  } else {
    await http.post(`/rfqs/${rfqId.value}/quotations`, body)
  }
  ElMessage.success('已保存')
  quoteDlg.value = false
  reload()
}

async function removeQuote(id: string) {
  await ElMessageBox.confirm('删除该报价？', '确认')
  await http.delete(`/quotations/${id}`)
  ElMessage.success('已删除')
  reload()
}

function openSampleDialog() {
  sampleBody.rfq_item_id = (ws.value?.rfq_items as { id: string }[])?.[0]?.id || ''
  sampleBody.manufacturing_partner_id = ''
  sampleBody.notes = ''
  sampleDlg.value = true
}

async function doConvertSample() {
  try {
    await http.post(`/rfqs/${rfqId.value}/convert-to-sample`, {
      rfq_item_id: sampleBody.rfq_item_id,
      manufacturing_partner_id: sampleBody.manufacturing_partner_id,
      notes: sampleBody.notes || null,
    })
    ElMessage.success('已创建样品，可在样品列表查看')
    sampleDlg.value = false
    reload()
  } catch {
    ElMessage.error('创建样品失败，请检查行项目与制造伙伴')
  }
}

function openOrderDialog() {
  orderBody.quote_id = undefined
  orderBody.rfq_item_id = (ws.value?.rfq_items as { id: string }[])?.[0]?.id
  orderBody.manufacturing_partner_id = ''
  orderBody.generate_milestones = false
  orderBody.notes = ''
  orderDlg.value = true
}

async function doConvertOrder() {
  if (!orderBody.manufacturing_partner_id) {
    ElMessage.error('请选择制造伙伴')
    return
  }
  try {
    await http.post(`/rfqs/${rfqId.value}/convert-to-order`, {
      quotation_id: orderBody.quote_id || null,
      rfq_item_id: orderBody.quote_id ? null : orderBody.rfq_item_id || null,
      manufacturing_partner_id: orderBody.manufacturing_partner_id,
      generate_milestones: orderBody.generate_milestones,
      notes: orderBody.notes || null,
    })
    ElMessage.success('已创建订单，可在订单列表查看')
    orderDlg.value = false
    reload()
  } catch {
    ElMessage.error('创建订单失败，请检查字段与报价')
  }
}

onMounted(async () => {
  await loadMeta()
  reload()
})
</script>
