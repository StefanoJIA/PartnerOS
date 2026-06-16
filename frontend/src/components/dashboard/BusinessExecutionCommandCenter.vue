<template>
  <section class="rounded border border-slate-200 bg-white p-4">
    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-slate-900">经营执行主链</h3>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把客户生命周期、项目机会、报价经验、产品验证、Partner 能力和交付风险合并成管理层每天可执行的经营判断。
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="primary" effect="plain">客户 {{ data?.summary.lifecycle_accounts ?? 0 }}</el-tag>
        <el-tag type="success" effect="plain">机会 {{ data?.summary.active_opportunities ?? 0 }}</el-tag>
        <el-tag type="warning" effect="plain">报价经验 {{ data?.summary.quote_learning_items ?? 0 }}</el-tag>
        <el-tag type="danger" effect="plain">交付风险 {{ data?.summary.delivery_risks ?? 0 }}</el-tag>
        <el-tag type="info" effect="plain">Partner 投入 {{ data?.summary.partner_investment_items ?? 0 }}</el-tag>
        <el-tag type="primary" effect="plain">商业资产 {{ data?.summary.commercial_intelligence_items ?? 0 }}</el-tag>
      </div>
    </div>

    <el-alert
      class="mb-4"
      type="warning"
      :closable="false"
      show-icon
      title="只读经营判断层：不自动发送外部消息、不改报价或订单状态、不记录 raw token、不把本地信息写成真实 staging evidence。"
    />

    <div v-if="!data" class="rounded border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
      正在加载经营执行主链。
    </div>

    <template v-else>
      <div class="grid gap-3 lg:grid-cols-3">
        <div
          v-for="item in data.executive_decisions"
          :key="item.decision_id"
          class="rounded border border-slate-100 bg-slate-50 p-3"
        >
          <div class="mb-2 flex items-start justify-between gap-2">
            <h4 class="font-semibold text-slate-900">{{ item.question }}</h4>
            <el-tag :type="priorityType(item.priority)" effect="plain">{{ item.priority }}</el-tag>
          </div>
          <p class="text-sm text-slate-700">{{ item.answer }}</p>
          <p class="mt-2 text-xs text-slate-500">Owner: {{ item.owner }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ item.next_action }}</p>
          <el-button class="mt-2" size="small" type="primary" plain @click="go(item.path)">进入处理</el-button>
        </div>
      </div>

      <section class="mt-4 rounded border border-indigo-100 bg-indigo-50/40 p-3">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4 class="font-semibold text-slate-900">商业智能资产</h4>
            <p class="mt-1 text-xs text-slate-600">
              把赢输原因、客户价值、Partner 绩效、产品市场匹配、收入预测和 Account 360 汇总成经营判断，不自动外发、不改状态。
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-tag size="small" effect="plain">Win/Loss {{ safeCommercial.win_loss.length }}</el-tag>
            <el-tag size="small" effect="plain">客户价值 {{ safeCommercial.customer_value.length }}</el-tag>
            <el-tag size="small" effect="plain">PMF {{ safeCommercial.product_market_fit.length }}</el-tag>
          </div>
        </div>
        <div class="grid gap-3 lg:grid-cols-3">
          <div class="rounded border border-white bg-white p-3">
            <div class="mb-2 flex items-center justify-between">
              <h5 class="text-sm font-semibold text-slate-900">未来收入来自哪里</h5>
              <el-tag size="small" type="success" effect="plain">
                {{ money(safeCommercial.revenue_forecast.weighted_opportunity_amount) }}
              </el-tag>
            </div>
            <p class="text-xs text-slate-600">
              报价池 {{ money(safeCommercial.revenue_forecast.open_quote_amount) }}，
              加权报价 {{ money(safeCommercial.revenue_forecast.weighted_quote_amount) }}。
            </p>
            <p class="mt-2 text-xs text-slate-700">{{ safeCommercial.revenue_forecast.next_action }}</p>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag
                v-for="project in forecastProjects(safeCommercial.revenue_forecast).slice(0, 3)"
                :key="String(project.name)"
                size="small"
                effect="plain"
              >
                {{ project.name }} {{ project.probability }}%
              </el-tag>
            </div>
          </div>

          <div class="rounded border border-white bg-white p-3">
            <div class="mb-2 flex items-center justify-between">
              <h5 class="text-sm font-semibold text-slate-900">谁最值得跟进</h5>
              <el-tag size="small" type="primary" effect="plain">Account 360</el-tag>
            </div>
            <div v-for="account in safeCommercial.account_360.slice(0, 3)" :key="String(account.account_key)" class="mb-2 last:mb-0">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-slate-800">{{ account.customer_name }}</span>
                <el-tag size="small" effect="plain">{{ account.current_stage }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ account.next_action }}</p>
              <p class="mt-1 text-xs text-slate-500">
                成交 {{ money(commercialValue(account).won_order_amount) }} / 报价 {{ money(commercialValue(account).historical_quote_amount) }}
              </p>
            </div>
          </div>

          <div class="rounded border border-white bg-white p-3">
            <div class="mb-2 flex items-center justify-between">
              <h5 class="text-sm font-semibold text-slate-900">什么正在获得市场验证</h5>
              <el-tag size="small" type="warning" effect="plain">Product-Market Fit</el-tag>
            </div>
            <div v-for="item in safeCommercial.product_market_fit.slice(0, 3)" :key="`${item.partner_focus}-${String(item.product_focus)}`" class="mb-2 last:mb-0">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" effect="plain">{{ item.partner_focus }}</el-tag>
                <el-tag size="small" :type="productValidationType(String(item.fit_status || 'baseline_only'))" effect="plain">
                  {{ productValidationLabel(String(item.fit_status || 'baseline_only')) }}
                </el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-700">{{ item.next_action }}</p>
              <p class="mt-1 text-xs text-slate-500">
                购买因素：{{ listLabel(item.purchase_factors).slice(0, 5).join(' / ') || '待沉淀' }}
              </p>
            </div>
          </div>
        </div>

        <div class="mt-3 grid gap-3 lg:grid-cols-3">
          <div class="rounded border border-white bg-white p-3">
            <h5 class="mb-2 text-sm font-semibold text-slate-900">为什么赢 / 为什么输</h5>
            <div v-for="item in safeCommercial.win_loss.slice(0, 3)" :key="`${item.source_type}-${item.source_id}`" class="mb-2 last:mb-0">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="item.outcome === 'won' ? 'success' : 'danger'" effect="plain">{{ item.outcome }}</el-tag>
                <span class="text-xs text-slate-700">{{ item.customer }}</span>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ item.commercial_lesson }}</p>
            </div>
          </div>
          <div class="rounded border border-white bg-white p-3">
            <h5 class="mb-2 text-sm font-semibold text-slate-900">哪个 Partner 值得投入</h5>
            <div v-for="item in safeCommercial.partner_performance.slice(0, 3)" :key="String(item.partner_id)" class="mb-2 last:mb-0">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-slate-800">{{ item.partner_name }}</span>
                <el-tag size="small" effect="plain">赢单率 {{ percent(item.win_rate) }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">
                订单 {{ money(item.order_amount) }} / 反馈问题 {{ item.feedback_issue_count ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500">{{ item.next_action }}</p>
            </div>
          </div>
          <div class="rounded border border-white bg-white p-3">
            <h5 class="mb-2 text-sm font-semibold text-slate-900">客户价值排序</h5>
            <div v-for="item in safeCommercial.customer_value.slice(0, 3)" :key="String(item.company_id)" class="mb-2 last:mb-0">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-slate-800">{{ item.customer_name }}</span>
                <el-tag size="small" effect="plain">{{ item.strategic_value }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">
                报价 {{ money(item.historical_quote_amount) }} / 成交 {{ money(item.won_order_amount) }} / 转化 {{ percent(item.conversion_rate) }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section class="mt-4 rounded border border-slate-100 p-3">
        <div class="mb-2 flex items-center justify-between">
          <div>
            <h4 class="font-semibold text-slate-900">客户账户主线</h4>
            <p class="mt-1 text-xs text-slate-500">
              按客户聚合线索、机会、报价、订单和反馈，显示最高阶段、当前阻碍和下一步协同动作。
            </p>
          </div>
          <el-button size="small" link type="primary" @click="go('/growth-operations')">推进机会</el-button>
        </div>
        <el-table :data="data.account_lifecycle.slice(0, 6)" size="small" border empty-text="暂无客户账户主线数据">
          <el-table-column label="客户 / 当前阶段" min-width="210">
            <template #default="{ row }">
              <div class="font-medium text-slate-800">{{ row.customer_name }}</div>
              <div class="mt-1 flex flex-wrap gap-1">
                <el-tag size="small" effect="plain">{{ row.current_stage }}</el-tag>
                <el-tag size="small" :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ row.partner_focus || 'future partner' }}</el-tag>
              </div>
              <div class="mt-1 text-xs text-slate-500">{{ sourceCountsLabel(row.source_counts) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="判断依据 / 下一步" min-width="330">
            <template #default="{ row }">
              <p class="text-xs text-slate-500">{{ row.decision_reason }}</p>
              <p class="mt-1 text-xs text-slate-700">{{ row.next_action }}</p>
              <div v-if="row.commercial_health" class="mt-2 rounded border border-blue-100 bg-blue-50 p-2">
                <div class="flex flex-wrap items-center gap-1">
                  <el-tag size="small" :type="commercialHealthType(row.commercial_health.health)" effect="plain">
                    {{ commercialHealthLabel(row.commercial_health.health) }}
                  </el-tag>
                  <el-tag size="small" effect="plain">{{ row.commercial_health.business_focus }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ row.commercial_health.score }}/100</el-tag>
                </div>
                <p class="mt-1 text-xs text-slate-700">{{ row.commercial_health.next_best_action }}</p>
              </div>
              <div v-if="row.stage_progression" class="mt-2 rounded border border-emerald-100 bg-emerald-50 p-2">
                <div class="flex flex-wrap items-center gap-1">
                  <el-tag size="small" :type="stageGateType(row.stage_progression.health)" effect="plain">
                    {{ stageGateLabel(row.stage_progression.health) }}
                  </el-tag>
                  <el-tag size="small" effect="plain">
                    {{ row.stage_progression.current_stage }} → {{ row.stage_progression.next_stage || '复购维护' }}
                  </el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ row.stage_progression.handoff_object }}</el-tag>
                </div>
                <p class="mt-1 text-xs text-slate-700">{{ row.stage_progression.recommended_action }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ row.stage_progression.why_now }}</p>
                <div v-if="row.stage_progression.missing_inputs.length" class="mt-1 flex flex-wrap gap-1">
                  <el-tag
                    v-for="item in row.stage_progression.missing_inputs.slice(0, 3)"
                    :key="item"
                    size="small"
                    type="warning"
                    effect="plain"
                  >
                    {{ item }}
                  </el-tag>
                </div>
              </div>
              <p v-if="row.open_blockers.length" class="mt-1 text-xs text-rose-600">{{ row.open_blockers[0] }}</p>
              <div class="mt-1 flex flex-wrap gap-1">
                <el-tag v-for="impact in row.readiness_impact.slice(0, 3)" :key="impact" size="small" effect="plain">
                  {{ impact }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="入口" width="90">
            <template #default="{ row }">
              <el-button size="small" link type="primary" @click="go(row.stage_progression?.recommended_entry_path || row.active_paths[0] || '/')">打开</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <div class="mt-4 grid gap-4 xl:grid-cols-2">
        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">客户生命周期</h4>
            <el-button size="small" link type="primary" @click="go('/lead-intelligence')">客户开发</el-button>
          </div>
          <el-table :data="data.lifecycle.slice(0, 6)" size="small" border empty-text="暂无客户生命周期数据">
            <el-table-column label="客户 / 阶段" min-width="180">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.customer_name }}</div>
                <div class="mt-1 flex flex-wrap gap-1">
                  <el-tag size="small" effect="plain">{{ row.lifecycle_stage }}</el-tag>
                  <el-tag size="small" :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ lifecycleSourceLabel(row.source_type) }}</el-tag>
                </div>
                <div class="mt-1 text-xs text-slate-500">{{ row.partner_focus || 'future partner' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="下一步 / 阻碍" min-width="260">
              <template #default="{ row }">
                <p class="text-xs text-slate-500">{{ row.current_signal }}</p>
                <p class="text-xs text-slate-700">{{ row.next_action }}</p>
                <p v-if="row.blocker" class="mt-1 text-xs text-rose-600">{{ row.blocker }}</p>
                <div class="mt-1 flex flex-wrap gap-1">
                  <el-tag v-for="impact in row.readiness_impact.slice(0, 3)" :key="impact" size="small" effect="plain">
                    {{ impact }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">项目机会管线</h4>
            <el-button size="small" link type="primary" @click="go('/growth-operations')">增长运营</el-button>
          </div>
          <el-table :data="data.opportunities.slice(0, 6)" size="small" border empty-text="暂无机会数据">
            <el-table-column label="机会 / Partner" min-width="210">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.opportunity_name }}</div>
                <div class="mt-1 text-xs text-slate-500">{{ row.partner_focus || 'future partner' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="概率 / 风险" min-width="220">
              <template #default="{ row }">
                <el-progress :percentage="row.probability" :stroke-width="8" />
                <p class="mt-1 text-xs text-slate-600">{{ row.risk }}</p>
                <div v-if="row.stage_gate" class="mt-2 rounded border border-blue-100 bg-blue-50 p-2">
                  <div class="flex flex-wrap items-center gap-1">
                    <el-tag size="small" :type="stageGateType(row.stage_gate.health)" effect="plain">
                      {{ stageGateLabel(row.stage_gate.health) }}
                    </el-tag>
                    <el-tag size="small" effect="plain">{{ row.stage_gate.current_stage_label }}</el-tag>
                  </div>
                  <p class="mt-1 text-xs text-slate-700">{{ row.stage_gate.next_best_action }}</p>
                  <div v-if="row.partner_fit?.partner_id" class="mt-2 rounded border border-emerald-100 bg-emerald-50 p-2">
                    <div class="flex flex-wrap items-center gap-1">
                      <el-tag size="small" type="success" effect="plain">{{ row.partner_fit.partner_name }}</el-tag>
                      <el-tag size="small" type="info" effect="plain">匹配 {{ row.partner_fit.fit_score }}/100</el-tag>
                      <el-tag size="small" effect="plain">{{ row.partner_fit.business_focus }}</el-tag>
                    </div>
                    <p class="mt-1 text-xs text-slate-700">{{ row.partner_fit.next_best_action }}</p>
                  </div>
                  <div v-if="row.execution_context" class="mt-2 rounded border border-emerald-100 bg-emerald-50 p-2">
                    <div class="flex flex-wrap items-center gap-1">
                      <el-tag size="small" :type="executionHealthType(row.execution_context.health)" effect="plain">
                        {{ executionHealthLabel(row.execution_context.health) }}
                      </el-tag>
                      <el-tag size="small" type="info" effect="plain">报价 {{ row.execution_context.linked_quote_count || 0 }}</el-tag>
                      <el-tag size="small" type="info" effect="plain">订单 {{ row.execution_context.linked_order_count || 0 }}</el-tag>
                      <el-tag v-if="row.execution_context.feedback?.open" size="small" type="warning" effect="plain">
                        反馈 {{ row.execution_context.feedback.open }}
                      </el-tag>
                    </div>
                    <p class="mt-1 text-xs text-slate-700">
                      {{ row.execution_context.next_best_action || row.execution_context.conversion_signal?.next_best_action }}
                    </p>
                  </div>
                  <div v-if="row.stage_gate.missing_inputs.length" class="mt-1 flex flex-wrap gap-1">
                    <el-tag v-for="item in row.stage_gate.missing_inputs.slice(0, 3)" :key="item" size="small" type="warning" effect="plain">
                      缺 {{ stageGateInputLabel(item) }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">报价经验沉淀</h4>
            <el-button size="small" link type="primary" @click="go('/quotes')">报价</el-button>
          </div>
          <el-table :data="data.quotations.slice(0, 5)" size="small" border empty-text="暂无报价数据">
            <el-table-column label="报价 / 状态" min-width="150">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.quote_number }}</div>
                <el-tag class="mt-1" size="small" effect="plain">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="经验缺口" min-width="260">
              <template #default="{ row }">
                <p class="text-xs text-slate-700">{{ row.outcome_signal }}</p>
                <p class="mt-1 text-xs text-amber-700">{{ row.learning_signal }}</p>
                <div v-if="row.commercial_intelligence" class="mt-2 rounded border border-blue-100 bg-blue-50 p-2">
                  <div class="flex flex-wrap items-center gap-1">
                    <el-tag size="small" :type="priorityType(row.commercial_intelligence.priority)" effect="plain">
                      {{ row.commercial_intelligence.priority }}
                    </el-tag>
                    <el-tag size="small" effect="plain">{{ row.commercial_intelligence.business_focus }}</el-tag>
                    <el-tag size="small" type="info" effect="plain">{{ row.commercial_intelligence.score }}/100</el-tag>
                    <el-tag
                      v-if="row.commercial_intelligence.market_response_review_needed"
                      size="small"
                      type="success"
                      effect="plain"
                    >
                      Market Response
                    </el-tag>
                  </div>
                  <p class="mt-1 text-xs text-slate-700">{{ row.commercial_intelligence.next_best_action }}</p>
                  <p v-if="row.commercial_intelligence.dimension_review_needs.length" class="mt-1 text-xs text-slate-500">
                    维度缺口：{{ row.commercial_intelligence.dimension_review_needs.slice(0, 4).join(' / ') }}
                  </p>
                </div>
                <div v-if="row.partner_readiness?.partners?.length" class="mt-2 rounded border border-emerald-100 bg-emerald-50 p-2">
                  <div class="flex flex-wrap items-center gap-1">
                    <el-tag size="small" :type="priorityType(row.partner_readiness.priority)" effect="plain">
                      {{ row.partner_readiness.priority }}
                    </el-tag>
                    <el-tag size="small" type="success" effect="plain">
                      {{ row.partner_readiness.partners[0].partner_name }}
                    </el-tag>
                    <el-tag size="small" type="info" effect="plain">
                      {{ row.partner_readiness.partners[0].readiness_score }}/100
                    </el-tag>
                  </div>
                  <p class="mt-1 text-xs text-slate-700">{{ row.partner_readiness.next_best_action }}</p>
                  <p v-if="row.partner_readiness.missing_inputs.length" class="mt-1 text-xs text-slate-500">
                    Partner 缺口：{{ row.partner_readiness.missing_inputs.slice(0, 3).join(' / ') }}
                  </p>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">产品 / Market Intelligence</h4>
            <el-button size="small" link type="primary" @click="go('/market-response')">市场响应</el-button>
          </div>
          <div class="space-y-2">
            <div v-for="item in data.products.slice(0, 5)" :key="item.partner_focus + item.validation_signal" class="rounded bg-slate-50 p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" effect="plain">{{ item.partner_focus }}</el-tag>
                <el-tag v-for="dimension in item.dimensions.slice(0, 5)" :key="dimension" size="small" type="info" effect="plain">
                  {{ dimension }}
                </el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-700">{{ item.validation_signal }}</p>
              <p class="mt-1 text-xs text-rose-600">{{ item.risk }}</p>
              <div v-if="item.validation_context" class="mt-2 rounded border border-cyan-100 bg-cyan-50 p-2">
                <div class="flex flex-wrap items-center gap-1">
                  <el-tag size="small" :type="productValidationType(item.validation_context.health)" effect="plain">
                    {{ productValidationLabel(item.validation_context.health) }}
                  </el-tag>
                  <el-tag size="small" effect="plain">{{ item.validation_context.priority }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">机会 {{ item.validation_context.evidence_counts.opportunities }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">报价 {{ item.validation_context.evidence_counts.quotes }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">订单 {{ item.validation_context.evidence_counts.orders }}</el-tag>
                  <el-tag v-if="item.validation_context.evidence_counts.feedback" size="small" type="warning" effect="plain">
                    反馈 {{ item.validation_context.evidence_counts.feedback }}
                  </el-tag>
                  <el-tag v-if="item.validation_context.evidence_counts.delivery_risks" size="small" type="danger" effect="plain">
                    交付风险 {{ item.validation_context.evidence_counts.delivery_risks }}
                  </el-tag>
                </div>
                <p class="mt-1 text-xs text-slate-700">{{ item.validation_context.next_best_action }}</p>
                <div v-if="item.validation_context.readiness_impact.length" class="mt-1 flex flex-wrap gap-1">
                  <el-tag
                    v-for="impact in item.validation_context.readiness_impact.slice(0, 4)"
                    :key="impact"
                    size="small"
                    effect="plain"
                  >
                    {{ impact }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">Partner Intelligence</h4>
            <el-button size="small" link type="primary" @click="go('/partner-onboarding')">Partner 接入</el-button>
          </div>
          <div class="grid gap-2 md:grid-cols-2">
            <div v-for="item in data.partners.slice(0, 6)" :key="item.partner_id" class="rounded bg-slate-50 p-2">
              <div class="font-medium text-slate-800">{{ item.partner_name }}</div>
              <p class="mt-1 text-xs text-slate-600">{{ item.readiness_level }} / {{ item.delivery_ability }}</p>
              <p class="mt-1 text-xs text-rose-600">{{ item.risk_assessment }}</p>
              <div v-if="item.capability_intelligence" class="mt-2 rounded border border-indigo-100 bg-indigo-50 p-2">
                <div class="flex flex-wrap items-center gap-1">
                  <el-tag size="small" :type="priorityType(item.capability_intelligence.investment_priority)" effect="plain">
                    {{ item.capability_intelligence.investment_priority }}
                  </el-tag>
                  <el-tag size="small" effect="plain">{{ item.capability_intelligence.business_focus }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ item.capability_intelligence.score }}/100</el-tag>
                </div>
                <p class="mt-1 text-xs text-slate-700">{{ item.capability_intelligence.next_best_action }}</p>
                <p v-if="item.capability_intelligence.missing_inputs.length" class="mt-1 text-xs text-slate-500">
                  缺口：{{ item.capability_intelligence.missing_inputs.slice(0, 3).join(' / ') }}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">项目交付透明度</h4>
            <el-button size="small" link type="primary" @click="go('/orders')">订单</el-button>
          </div>
          <el-table :data="data.delivery.slice(0, 5)" size="small" border empty-text="暂无交付数据">
            <el-table-column label="订单 / 风险" min-width="150">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.order_number }}</div>
                <el-tag class="mt-1" size="small" :type="riskType(row.risk_level)" effect="plain">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="交付信号" min-width="280">
              <template #default="{ row }">
                <p class="text-xs text-slate-700">{{ row.production_signal }}</p>
                <p class="mt-1 text-xs text-slate-600">{{ row.shipment_signal }}</p>
                <p class="mt-1 text-xs text-amber-700">{{ row.repeat_business_risk }}</p>
                <div v-if="row.fulfillment_intelligence" class="mt-2 rounded border border-orange-100 bg-orange-50 p-2">
                  <div class="flex flex-wrap items-center gap-1">
                    <el-tag size="small" :type="riskType(row.fulfillment_intelligence.risk_level)" effect="plain">
                      {{ row.fulfillment_intelligence.business_focus }}
                    </el-tag>
                    <el-tag v-if="row.fulfillment_intelligence.quote_business_focus" size="small" effect="plain">
                      {{ row.fulfillment_intelligence.quote_business_focus }}
                    </el-tag>
                    <el-tag
                      v-for="impact in row.fulfillment_intelligence.readiness_impact.slice(0, 2)"
                      :key="impact"
                      size="small"
                      type="warning"
                      effect="plain"
                    >
                      {{ impact }}
                    </el-tag>
                  </div>
                  <p class="mt-1 text-xs text-slate-700">{{ row.fulfillment_intelligence.next_best_action }}</p>
                  <p v-if="row.fulfillment_intelligence.quote_dimension_gaps.length" class="mt-1 text-xs text-slate-500">
                    报价维度待兑现：{{ row.fulfillment_intelligence.quote_dimension_gaps.slice(0, 4).join(' / ') }}
                  </p>
                  <div
                    v-if="row.fulfillment_intelligence.partner_execution_readiness?.partners?.length"
                    class="mt-2 rounded border border-amber-200 bg-white p-2"
                  >
                    <div class="flex flex-wrap items-center gap-1">
                      <el-tag size="small" type="warning" effect="plain">
                        {{ row.fulfillment_intelligence.partner_execution_readiness.priority }}
                      </el-tag>
                      <el-tag size="small" effect="plain">
                        {{ row.fulfillment_intelligence.partner_execution_readiness.partners[0].partner_name }}
                      </el-tag>
                      <el-tag size="small" effect="plain">
                        {{ row.fulfillment_intelligence.partner_execution_readiness.partners[0].handoff_stage }}
                      </el-tag>
                    </div>
                    <p class="mt-1 text-xs text-slate-700">
                      {{ row.fulfillment_intelligence.partner_execution_readiness.next_best_action }}
                    </p>
                    <p
                      v-if="row.fulfillment_intelligence.partner_execution_readiness.missing_inputs.length"
                      class="mt-1 text-xs text-amber-700"
                    >
                      Partner 缺口：{{ row.fulfillment_intelligence.partner_execution_readiness.missing_inputs.slice(0, 3).join(' / ') }}
                    </p>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { BusinessExecution } from '@/api/dashboard'

const props = defineProps<{
  data: BusinessExecution | null
}>()

const router = useRouter()

const defaultCommercial = {
  win_loss: [] as Array<Record<string, unknown>>,
  customer_value: [] as Array<Record<string, unknown>>,
  partner_performance: [] as Array<Record<string, unknown>>,
  product_market_fit: [] as Array<Record<string, unknown>>,
  revenue_forecast: {
    weighted_opportunity_amount: 0,
    open_quote_amount: 0,
    weighted_quote_amount: 0,
    next_action: '等待商业智能数据加载。',
    high_probability_projects: [] as Array<Record<string, unknown>>,
  } as Record<string, unknown>,
  account_360: [] as Array<Record<string, unknown>>,
}

const safeCommercial = computed(() => props.data?.commercial_intelligence || defaultCommercial)

function go(path: string) {
  router.push(path)
}

function asNumber(value: unknown) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? number : 0
}

function money(value: unknown) {
  return `$${asNumber(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function percent(value: unknown) {
  return `${Math.round(asNumber(value) * 100)}%`
}

function listLabel(value: unknown) {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

function commercialValue(account: Record<string, unknown>) {
  return (account.commercial_value || {}) as Record<string, unknown>
}

function forecastProjects(forecast: Record<string, unknown>) {
  return Array.isArray(forecast.high_probability_projects)
    ? (forecast.high_probability_projects as Array<Record<string, unknown>>)
    : []
}

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  return 'info'
}

function riskType(risk: string) {
  if (risk === 'high') return 'danger'
  if (risk === 'medium') return 'warning'
  return 'info'
}

function commercialHealthLabel(value: string) {
  const labels: Record<string, string> = {
    conversion_ready: '成交推进',
    pipeline_active: '项目推进',
    delivery_risk: '交付风险',
    after_sales_attention: '售后维护',
    blocked: '推进阻塞',
    nurture: '继续培育',
  }
  return labels[value] || value || '待判断'
}

function commercialHealthType(value: string) {
  if (value === 'delivery_risk' || value === 'blocked') return 'danger'
  if (value === 'after_sales_attention') return 'warning'
  if (value === 'conversion_ready') return 'success'
  if (value === 'pipeline_active') return 'primary'
  return 'info'
}

function stageGateLabel(health: string) {
  const labels: Record<string, string> = {
    blocked: '阻塞',
    needs_input: '需补输入',
    ready_to_advance: '可评审推进',
    closed: '已关闭',
  }
  return labels[health] || health
}

function stageGateType(health: string) {
  if (health === 'blocked') return 'danger'
  if (health === 'needs_input') return 'warning'
  if (health === 'ready_to_advance') return 'success'
  return 'info'
}

function executionHealthLabel(health: string) {
  const labels: Record<string, string> = {
    needs_quote: '需要报价',
    quote_follow_up: '报价跟进',
    order_converted: '已转订单',
    delivery_or_feedback_risk: '交付/反馈风险',
    feedback_review: '反馈复盘',
    stage_inputs_needed: '阶段输入不足',
    not_evaluated: '待评估',
  }
  return labels[health] || health
}

function executionHealthType(health: string) {
  if (health === 'delivery_or_feedback_risk' || health === 'feedback_review') return 'danger'
  if (health === 'needs_quote' || health === 'quote_follow_up' || health === 'stage_inputs_needed') return 'warning'
  if (health === 'order_converted') return 'success'
  return 'info'
}

function productValidationLabel(health: string) {
  const labels: Record<string, string> = {
    needs_product_review: '需要产品复盘',
    customer_safe_evidence_ready: '客户可见证据就绪',
    market_validation_in_progress: '市场验证中',
    baseline_only: '仅基线维度',
  }
  return labels[health] || health
}

function productValidationType(health: string) {
  if (health === 'needs_product_review') return 'danger'
  if (health === 'market_validation_in_progress') return 'warning'
  if (health === 'customer_safe_evidence_ready') return 'success'
  return 'info'
}

function stageGateInputLabel(value: string) {
  const labels: Record<string, string> = {
    owner: '负责人',
    next_action: '下一步',
    customer_or_segment: '客户/分群',
    product_focus: '产品方向',
    project_size_or_value: '项目规模/金额',
    risk: '风险',
    competition_or_alternative: '竞争/替代方案',
    linked_quote: '关联报价',
    expected_close_date: '预计关闭日期',
    linked_order: '关联订单',
    won_reason: '成交原因',
    lost_reason: '丢单原因',
    hold_reason: '暂停原因',
  }
  return labels[value] || value
}

function lifecycleSourceLabel(sourceType: string) {
  if (sourceType === 'lead') return '线索'
  if (sourceType === 'opportunity') return '机会'
  if (sourceType === 'quote') return '报价'
  if (sourceType === 'order') return '订单'
  if (sourceType === 'feedback') return '反馈'
  return sourceType
}
function sourceCountsLabel(counts: Record<string, number>) {
  const labels: Record<string, string> = {
    lead: '线索',
    opportunity: '机会',
    quote: '报价',
    order: '订单',
    feedback: '反馈',
  }
  return Object.entries(counts)
    .map(([key, value]) => `${labels[key] || key} ${value}`)
    .join(' / ')
}
</script>
