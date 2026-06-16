<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">商业智能工作台</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把 Win/Loss、客户价值、Partner 绩效、产品市场匹配、收入预测和 Account 360 组织成管理层可查询的商业经验库。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="go('/')">返回行动看板</el-button>
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="内部商业智能层：不自动发送外部消息、不改报价或订单状态、不暴露成本、利润、供应商私密信息、raw token 或客户不可见字段。"
    />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <template v-if="data">
      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">Management Commercial Brief</h3>
            <p class="mt-1 text-sm text-slate-600">
              Standardized answers for the six commercial questions: answer, evidence, next action, source assets, and safety boundary.
            </p>
          </div>
          <el-tag type="primary" effect="plain">{{ managementBrief.length }} answers</el-tag>
        </div>

        <div class="grid gap-3 lg:grid-cols-2">
          <div
            v-for="item in managementBrief"
            :key="String(item.key || item.question)"
            class="rounded border border-slate-100 bg-slate-50 p-3"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ item.question }}</p>
                <h4 class="mt-1 text-sm font-semibold text-slate-900">{{ item.answer }}</h4>
              </div>
              <el-tag size="small" effect="plain">{{ item.owner || 'business owner' }}</el-tag>
            </div>
            <p class="mt-2 text-sm text-slate-700">{{ item.evidence }}</p>
            <p class="mt-2 text-xs text-slate-600">Next action: {{ item.recommended_action }}</p>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag
                v-for="asset in textList(item.source_assets).slice(0, 4)"
                :key="asset"
                size="small"
                type="info"
                effect="plain"
              >
                {{ asset }}
              </el-tag>
              <el-tag
                v-for="focus in textList(item.product_focus).slice(0, 3)"
                :key="focus"
                size="small"
                effect="plain"
              >
                {{ focus }}
              </el-tag>
            </div>
            <el-button class="mt-2" size="small" link type="primary" @click="go(String(item.path || '/'))">
              Open source object
            </el-button>
          </div>
        </div>

        <el-alert
          class="mt-3"
          type="warning"
          :closable="false"
          show-icon
          title="Brief is internal only: no external sending, no automatic quote/order status changes, and no cost, margin, supplier-private notes, raw token, or customer-unsafe fields."
        />
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">管理层今天能回答什么</h3>
            <p class="mt-1 text-sm text-slate-600">
              这些答案来自真实业务对象的只读聚合，可继续跳转到客户、报价、订单、Market Response 或 Partner 接入页面处理。
            </p>
          </div>
          <div class="flex flex-wrap gap-1">
            <el-tag type="success" effect="plain">加权收入 {{ money(snapshot.total_weighted_revenue) }}</el-tag>
            <el-tag type="primary" effect="plain">预测质量 {{ snapshot.forecast_quality_score ?? 0 }}/100</el-tag>
            <el-tag type="warning" effect="plain">风险收入 {{ money(snapshot.at_risk_weighted_amount) }}</el-tag>
          </div>
        </div>

        <div class="grid gap-3 lg:grid-cols-3">
          <div
            v-for="section in managementSections"
            :key="section.key"
            class="rounded border border-slate-100 bg-slate-50 p-3"
          >
            <div class="mb-2 flex items-start justify-between gap-2">
              <div>
                <h4 class="text-sm font-semibold text-slate-900">{{ section.title }}</h4>
                <p class="mt-1 text-xs text-slate-500">{{ section.description }}</p>
              </div>
              <el-tag size="small" effect="plain">{{ section.items.length }}</el-tag>
            </div>
            <div v-for="item in section.items.slice(0, 3)" :key="rowKey(item)" class="mb-3 last:mb-0">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="priorityType(String(item.priority || section.priority))" effect="plain">
                  {{ item.priority || section.priority }}
                </el-tag>
                <el-tag v-if="item.source_asset" size="small" type="info" effect="plain">{{ item.source_asset }}</el-tag>
              </div>
              <p class="mt-1 text-sm font-medium text-slate-800">{{ item.title || item.customer_name || item.name || item.partner_name || item.product_family || '商业对象' }}</p>
              <p class="mt-1 text-xs text-slate-600">{{ item.reason || item.next_action || item.management_answer || item.commercial_lesson || item.risk_reason || '等待更多商业证据。' }}</p>
              <el-button v-if="item.path" class="mt-1" size="small" link type="primary" @click="go(String(item.path))">进入来源</el-button>
            </div>
            <p v-if="!section.items.length" class="text-sm text-slate-500">暂无可用商业证据。</p>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">六类商业资产覆盖</h3>
            <p class="mt-1 text-sm text-slate-600">每个资产都回答一个管理问题，避免只展示分散后台数据。</p>
          </div>
          <el-tag type="primary" effect="plain">商业资产 {{ data.summary.commercial_intelligence_items }}</el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="asset in assetMap" :key="String(asset.asset)" class="rounded border border-slate-100 p-3">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ asset.asset }}</p>
                <p class="mt-1 text-xs text-slate-600">{{ asset.answers }}</p>
              </div>
              <el-tag size="small" effect="plain">{{ asset.items ?? 0 }}</el-tag>
            </div>
            <el-button class="mt-2" size="small" link type="primary" @click="go(String(asset.path || '/'))">查看业务入口</el-button>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">商业经验库查询</h3>
            <p class="mt-1 text-sm text-slate-600">
              按 partner、产品线、购买因素或客户查看可复用经验：为什么赢输、哪些因素影响成交、哪些账户需要下一次商业动作。
            </p>
          </div>
          <div class="flex flex-wrap gap-1">
            <el-tag type="primary" effect="plain">原因簇 {{ winLossReasonClusters.length }}</el-tag>
            <el-tag type="success" effect="plain">PMF 购买因素 {{ pmfBuyingFactors.length }}</el-tag>
            <el-tag type="warning" effect="plain">推荐账户 {{ accountRecommendations.length }}</el-tag>
            <el-tag type="info" effect="plain">客户价值 {{ customerValueRows.length }}</el-tag>
            <el-tag type="info" effect="plain">Partner 绩效 {{ partnerPerformanceRows.length }}</el-tag>
            <el-tag type="info" effect="plain">收入预测 {{ revenueForecastRows.length }}</el-tag>
          </div>
        </div>

        <div class="mb-3 grid gap-2 md:grid-cols-4">
          <el-select v-model="selectedPartner" clearable filterable placeholder="Partner">
            <el-option v-for="item in partnerOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedProduct" clearable filterable placeholder="产品线">
            <el-option v-for="item in productOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedFactor" clearable filterable placeholder="购买因素">
            <el-option v-for="item in factorOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedCustomer" clearable filterable placeholder="客户">
            <el-option v-for="item in customerOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </div>

        <div class="grid gap-3 xl:grid-cols-4">
          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">为什么赢 / 输</h4>
            <p class="mt-1 text-xs text-slate-500">来自 Win/Loss reason clusters 和客户决策因素。</p>
            <div v-for="item in filteredReasonClusters.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="info" effect="plain">{{ primaryText(item, ['reason_category', 'factor', 'partner_name', 'partner_focus', 'product_focus'], '原因') }}</el-tag>
                <el-tag size="small" type="success" effect="plain">赢 {{ item.won ?? item.win_count ?? 0 }}</el-tag>
                <el-tag size="small" type="danger" effect="plain">输 {{ item.lost ?? item.loss_count ?? 0 }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ primaryText(item, ['next_quote_guidance', 'sample_lessons', 'reason'], '复盘原因后再复用到下一次报价。') }}</p>
            </div>
            <p v-if="!filteredReasonClusters.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无赢输原因。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">购买因素证据</h4>
            <p class="mt-1 text-xs text-slate-500">来自 PMF validated buying factors 和产品线证据。</p>
            <div v-for="item in filteredBuyingFactors.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="primary" effect="plain">{{ primaryText(item, ['factor', 'dimension', 'buying_factor', 'product_focus'], '购买因素') }}</el-tag>
                <el-tag size="small" effect="plain">{{ primaryText(item, ['partner_focus', 'partner', 'partner_name'], 'multi-partner') }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">
                证据 {{ item.evidence_count ?? item.evidence ?? 0 }} / 赢 {{ item.wins ?? 0 }} / 输 {{ item.losses ?? 0 }} / 反馈 {{ item.feedback ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500">{{ primaryText(item, ['next_action', 'management_answer'], '确认该因素是否应进入报价话术和客户可见材料。') }}</p>
              <el-button class="mt-1" size="small" link type="primary" @click="openProductMarketFitFactor(item)">Product-Market Fit factor detail</el-button>
            </div>
            <p v-if="!filteredBuyingFactors.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无购买因素证据。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">下一批客户动作</h4>
            <p class="mt-1 text-xs text-slate-500">来自 Account 360 推荐账户和下一商业动作。</p>
            <div v-for="item in filteredAccounts.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="priorityType(String(item.priority || 'P2'))" effect="plain">{{ item.priority || 'P2' }}</el-tag>
                <el-tag size="small" effect="plain">{{ item.current_stage || item.relationship_depth || 'account' }}</el-tag>
              </div>
              <p class="mt-1 text-sm font-medium text-slate-800">{{ item.customer_name || item.account_key }}</p>
              <el-button class="mt-1" size="small" link type="primary" @click="openAccount360(item)">Account 360 detail</el-button>
              <p class="mt-1 text-xs text-slate-600">{{ nextMotion(item).next_action || item.next_action || '查看 Account 360 后选择下一步。' }}</p>
              <el-button class="mt-1" size="small" link type="primary" @click="go(String(item.path || '/growth-operations'))">打开账户</el-button>
            </div>
            <p v-if="!filteredAccounts.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无推荐账户。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">下一次报价可复用</h4>
            <p class="mt-1 text-xs text-slate-500">把赢输经验转成报价、Campaign 和产品话术输入。</p>
            <div v-for="item in filteredDecisionFactors.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="warning" effect="plain">{{ primaryText(item, ['factor', 'decision_factor', 'reason_category'], '决策因素') }}</el-tag>
                <el-tag size="small" effect="plain">{{ primaryText(item, ['product_focus', 'product', 'product_family'], '产品线') }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ primaryText(item, ['next_quote_guidance', 'management_answer', 'commercial_lesson'], '复用前先确认客户语境和产品证据。') }}</p>
              <el-button class="mt-1" size="small" link type="primary" @click="openWinLossFactor(item)">Win/Loss factor detail</el-button>
            </div>
            <p v-if="!filteredDecisionFactors.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无报价经验。</p>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">商业资产明细</h3>
            <p class="mt-1 text-sm text-slate-600">按资产类型查看专用商业智能 API 产出的经营证据，继续处理时跳转到原始业务对象。</p>
          </div>
          <el-tag type="info" effect="plain">{{ activeAssetLabel }}</el-tag>
        </div>
        <el-tabs v-model="activeAsset">
          <el-tab-pane v-for="asset in assetSections" :key="asset.key" :label="asset.label" :name="asset.key">
            <el-table :data="asset.items.slice(0, 8)" size="small" border :empty-text="`${asset.label} 暂无数据`">
              <el-table-column label="对象" min-width="220">
                <template #default="{ row }">
                  <div class="font-medium text-slate-800">{{ row.title }}</div>
                  <div class="mt-1 flex flex-wrap gap-1">
                    <el-tag v-for="tag in row.tags.slice(0, 4)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="商业判断" min-width="360">
                <template #default="{ row }">
                  <p class="text-sm text-slate-700">{{ row.reason }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.nextAction }}</p>
                </template>
              </el-table-column>
              <el-table-column label="入口" width="120">
                <template #default="{ row }">
                  <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>

    <div v-else-if="!loading" class="rounded border border-slate-200 bg-white p-4 text-sm text-slate-500">
      暂无商业智能数据。
    </div>
    <el-drawer v-model="accountDetailVisible" title="Account 360 commercial profile" size="560px">
      <div v-loading="accountDetailLoading" class="space-y-4">
        <el-alert v-if="accountDetailError" type="error" :closable="false" :title="accountDetailError" />
        <template v-if="accountDetail">
          <section>
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 class="text-base font-semibold text-slate-900">{{ accountDetail.customer_name }}</h3>
                <p class="mt-1 text-sm text-slate-600">{{ detailSummary.management_answer || accountDetail.next_action }}</p>
              </div>
              <el-tag :type="priorityType(accountDetail.priority)" effect="plain">{{ accountDetail.priority }}</el-tag>
            </div>
            <p class="mt-2 text-xs text-slate-500">{{ detailSummary.why_now || accountDetail.decision_reason }}</p>
          </section>

          <section class="grid gap-2 sm:grid-cols-2">
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Weighted pipeline</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ money(asRecord(accountDetail.commercial_value).weighted_pipeline_amount) }}</p>
            </div>
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Won order amount</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ money(asRecord(accountDetail.commercial_value).won_order_amount) }}</p>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Commercial questions</h4>
            <div class="mt-2 space-y-2 text-sm text-slate-700">
              <p><span class="font-medium">Owner:</span> {{ detailQuestions.who_should_act }}</p>
              <p><span class="font-medium">Next action:</span> {{ detailQuestions.what_to_do_next }}</p>
              <p><span class="font-medium">Why this account:</span> {{ detailQuestions.why_this_account }}</p>
              <p><span class="font-medium">Blocks repeat:</span> {{ textList(detailQuestions.what_blocks_repeat).join(' / ') || 'None visible' }}</p>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Commercial asset coverage</h4>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag
                v-for="asset in coverageTags"
                :key="asset.key"
                size="small"
                :type="asset.covered ? 'success' : 'info'"
                effect="plain"
              >
                {{ asset.label }} {{ asset.covered ? 'ready' : 'empty' }}
              </el-tag>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Lifecycle timeline</h4>
            <div v-for="item in textTimeline.slice(0, 8)" :key="rowKey(item)" class="mt-2 rounded bg-slate-50 p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" effect="plain">{{ item.source_type }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ item.status }}</el-tag>
              </div>
              <p class="mt-1 text-sm text-slate-800">{{ item.label }}</p>
              <el-button v-if="item.path" class="mt-1" size="small" link type="primary" @click="go(String(item.path))">Open object</el-button>
            </div>
          </section>

          <el-alert type="warning" :closable="false" show-icon :title="accountDetail.customer_safe_boundary" />
        </template>
      </div>
    </el-drawer>

    <el-drawer v-model="pmfDetailVisible" title="Product-Market Fit factor detail" size="580px">
      <div v-loading="pmfDetailLoading" class="space-y-4">
        <el-alert v-if="pmfDetailError" type="error" :closable="false" :title="pmfDetailError" />
        <template v-if="pmfDetail">
          <section>
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 class="text-base font-semibold text-slate-900">{{ pmfDetail.factor }}</h3>
                <p class="mt-1 text-sm text-slate-600">{{ pmfDetail.next_action }}</p>
              </div>
              <el-tag type="primary" effect="plain">{{ asRecord(pmfDetail.summary).evidence_count ?? 0 }} evidence</el-tag>
            </div>
          </section>

          <section class="grid gap-2 sm:grid-cols-3">
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Product lines</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ asRecord(pmfDetail.summary).product_line_count ?? 0 }}</p>
            </div>
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Orders / feedback</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ asRecord(pmfDetail.summary).orders ?? 0 }} / {{ asRecord(pmfDetail.summary).feedback ?? 0 }}</p>
            </div>
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Order amount</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ money(asRecord(pmfDetail.summary).order_amount) }}</p>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Partner / product evidence</h4>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag v-for="item in pmfPartnerTags" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              <el-tag v-for="item in pmfProductTags" :key="item" size="small" type="success" effect="plain">{{ item }}</el-tag>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Buying factor evidence</h4>
            <div v-for="item in pmfEvidenceRows.slice(0, 6)" :key="rowKey(item)" class="mt-2 rounded bg-slate-50 p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="primary" effect="plain">{{ item.factor }}</el-tag>
                <el-tag size="small" effect="plain">{{ item.fit_status }}</el-tag>
                <el-tag size="small" type="success" effect="plain">wins {{ item.wins ?? 0 }}</el-tag>
                <el-tag size="small" type="danger" effect="plain">losses {{ item.losses ?? 0 }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ item.next_action }}</p>
              <el-button v-if="item.path" class="mt-1" size="small" link type="primary" @click="go(String(item.path))">Open source object</el-button>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Project experience / objections</h4>
            <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in [...pmfProjectExperience, ...pmfCustomerObjections].slice(0, 8)" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Customer-safe candidates vs internal-only</h4>
            <div class="mt-2 grid gap-2 sm:grid-cols-2">
              <div>
                <p class="text-xs font-medium text-slate-500">Customer-safe candidates</p>
                <el-tag v-for="item in pmfCustomerSafeCandidates" :key="item" class="mr-1 mt-1" size="small" type="success" effect="plain">{{ item }}</el-tag>
              </div>
              <div>
                <p class="text-xs font-medium text-slate-500">Internal-only boundaries</p>
                <el-tag v-for="item in pmfInternalOnlyBoundaries" :key="item" class="mr-1 mt-1" size="small" type="warning" effect="plain">{{ item }}</el-tag>
              </div>
            </div>
          </section>

          <section v-if="pmfCompetitors.length" class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Competitor / alternative signals</h4>
            <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in pmfCompetitors" :key="item">{{ item }}</li>
            </ul>
          </section>

          <el-alert type="warning" :closable="false" show-icon :title="pmfDetail.customer_safe_boundary" />
        </template>
      </div>
    </el-drawer>

    <el-drawer v-model="factorDetailVisible" title="Win/Loss factor detail" size="560px">
      <div v-loading="factorDetailLoading" class="space-y-4">
        <el-alert v-if="factorDetailError" type="error" :closable="false" :title="factorDetailError" />
        <template v-if="factorDetail">
          <section>
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 class="text-base font-semibold text-slate-900">{{ factorDetail.factor }}</h3>
                <p class="mt-1 text-sm text-slate-600">{{ factorDetail.next_action }}</p>
              </div>
              <el-tag type="primary" effect="plain">{{ asRecord(factorDetail.summary).record_count ?? 0 }} records</el-tag>
            </div>
          </section>

          <section class="grid gap-2 sm:grid-cols-3">
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Won</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ asRecord(factorDetail.summary).won ?? 0 }}</p>
            </div>
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Lost</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ asRecord(factorDetail.summary).lost ?? 0 }}</p>
            </div>
            <div class="rounded border border-slate-100 bg-slate-50 p-3">
              <p class="text-xs text-slate-500">Commercial amount</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ money(asRecord(factorDetail.summary).commercial_amount) }}</p>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Reusable quote guidance</h4>
            <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in factorGuidance.slice(0, 6)" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Partner / product coverage</h4>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag v-for="item in factorPartnerTags" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              <el-tag v-for="item in factorProductTags" :key="item" size="small" type="success" effect="plain">{{ item }}</el-tag>
            </div>
          </section>

          <section class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Experience samples</h4>
            <div v-for="item in factorItems.slice(0, 6)" :key="rowKey(item)" class="mt-2 rounded bg-slate-50 p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="String(item.outcome) === 'won' ? 'success' : String(item.outcome) === 'lost' ? 'danger' : 'info'" effect="plain">{{ item.outcome }}</el-tag>
                <el-tag size="small" effect="plain">{{ item.reason_category }}</el-tag>
              </div>
              <p class="mt-1 text-sm text-slate-800">{{ item.customer || item.quote_number || item.opportunity_name }}</p>
              <p class="mt-1 text-xs text-slate-600">{{ item.commercial_lesson }}</p>
              <el-button v-if="item.path" class="mt-1" size="small" link type="primary" @click="go(String(item.path))">Open source object</el-button>
            </div>
          </section>

          <section v-if="factorCompetitors.length" class="rounded border border-slate-100 p-3">
            <h4 class="text-sm font-semibold text-slate-900">Competitor / alternative signals</h4>
            <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in factorCompetitors" :key="item">{{ item }}</li>
            </ul>
          </section>

          <el-alert type="warning" :closable="false" show-icon :title="factorDetail.customer_safe_boundary" />
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchAccount360Detail,
  fetchAccount360Intelligence,
  fetchBusinessExecution,
  fetchCustomerValueIntelligence,
  fetchPartnerPerformanceIntelligence,
  fetchProductMarketFitFactorDetail,
  fetchProductMarketFitIntelligence,
  fetchRevenueForecastIntelligence,
  fetchWinLossFactorDetail,
  fetchWinLossIntelligenceDashboard,
  type Account360Detail,
  type Account360Intelligence,
  type BusinessExecution,
  type CustomerValueIntelligence,
  type PartnerPerformanceIntelligence,
  type ProductMarketFitFactorDetail,
  type ProductMarketFitIntelligence,
  type RevenueForecastIntelligence,
  type WinLossFactorDetail,
  type WinLossIntelligenceDashboard,
} from '@/api/dashboard'

type Row = Record<string, unknown>

const router = useRouter()
const loading = ref(false)
const error = ref('')
const data = ref<BusinessExecution | null>(null)
const winLossDashboard = ref<WinLossIntelligenceDashboard | null>(null)
const productMarketFit = ref<ProductMarketFitIntelligence | null>(null)
const pmfDetail = ref<ProductMarketFitFactorDetail | null>(null)
const pmfDetailVisible = ref(false)
const pmfDetailLoading = ref(false)
const pmfDetailError = ref('')
const account360 = ref<Account360Intelligence | null>(null)
const accountDetail = ref<Account360Detail | null>(null)
const accountDetailVisible = ref(false)
const accountDetailLoading = ref(false)
const accountDetailError = ref('')
const factorDetail = ref<WinLossFactorDetail | null>(null)
const factorDetailVisible = ref(false)
const factorDetailLoading = ref(false)
const factorDetailError = ref('')
const customerValue = ref<CustomerValueIntelligence | null>(null)
const partnerPerformance = ref<PartnerPerformanceIntelligence | null>(null)
const revenueForecast = ref<RevenueForecastIntelligence | null>(null)
const activeAsset = ref('account360')
const selectedPartner = ref('')
const selectedProduct = ref('')
const selectedFactor = ref('')
const selectedCustomer = ref('')

const commercial = computed(() => data.value?.commercial_intelligence)
const detailSummary = computed(() => asRecord(accountDetail.value?.detail_summary))
const detailQuestions = computed(() => asRecord(accountDetail.value?.commercial_questions))
const textTimeline = computed(() => asList(accountDetail.value?.object_timeline))
const factorItems = computed(() => asList(factorDetail.value?.items))
const factorGuidance = computed(() => textList(factorDetail.value?.next_quote_guidance))
const factorCompetitors = computed(() => textList(factorDetail.value?.competitor_signals))
const factorPartnerTags = computed(() =>
  uniqueText(asList(factorDetail.value?.partner_rollup).flatMap((item) => [item.name, item.partner_focus, item.partner_name])),
)
const factorProductTags = computed(() =>
  uniqueText(asList(factorDetail.value?.product_rollup).flatMap((item) => [item.name, item.product_focus, item.product_family])),
)
const pmfEvidenceRows = computed(() => asList(pmfDetail.value?.buying_factor_evidence))
const pmfProjectExperience = computed(() => textList(pmfDetail.value?.project_experience))
const pmfCustomerObjections = computed(() => textList(pmfDetail.value?.customer_objections))
const pmfCompetitors = computed(() => textList(pmfDetail.value?.competitor_signals))
const pmfCustomerSafeCandidates = computed(() => textList(pmfDetail.value?.customer_safe_candidates))
const pmfInternalOnlyBoundaries = computed(() => textList(pmfDetail.value?.internal_only_boundaries))
const pmfPartnerTags = computed(() =>
  uniqueText(asList(pmfDetail.value?.partner_rollup).flatMap((item) => [item.name, item.partner_focus, item.partner_name])),
)
const pmfProductTags = computed(() =>
  uniqueText(asList(pmfDetail.value?.product_rollup).flatMap((item) => [item.name, item.product_focus, item.product_family])),
)
const coverageTags = computed(() => {
  const coverage = asRecord(accountDetail.value?.commercial_asset_coverage)
  return [
    { key: 'lead', label: 'Lead', covered: Boolean(coverage.lead) },
    { key: 'opportunity', label: 'Opportunity', covered: Boolean(coverage.opportunity) },
    { key: 'quote', label: 'Quote', covered: Boolean(coverage.quote) },
    { key: 'order_delivery', label: 'Order/Delivery', covered: Boolean(coverage.order_delivery) },
    { key: 'feedback', label: 'Feedback', covered: Boolean(coverage.feedback) },
    { key: 'win_loss', label: 'Win/Loss', covered: Boolean(coverage.win_loss) },
    { key: 'repeat_business', label: 'Repeat', covered: Boolean(coverage.repeat_business) },
  ]
})
const executiveSummary = computed(() => asRecord(commercial.value?.executive_summary))
const managementBrief = computed(() => asList(executiveSummary.value.management_brief))
const questions = computed(() => asRecord(executiveSummary.value.management_questions))
const snapshot = computed(() => asRecord(executiveSummary.value.commercial_snapshot))
const assetMap = computed(() => asList(executiveSummary.value.asset_map))
const winLossReasonClusters = computed(() => [
  ...asList(winLossDashboard.value?.reason_clusters),
  ...asList(winLossDashboard.value?.partner_rollup),
  ...asList(winLossDashboard.value?.product_rollup),
])
const winLossDecisionFactors = computed(() => asList(winLossDashboard.value?.decision_factor_rows))
const pmfBuyingFactors = computed(() => [
  ...asList(productMarketFit.value?.validated_buying_factors).flatMap((item) => expandPmfFactorRows(item)),
  ...asList(productMarketFit.value?.top_product_lines).flatMap((item) => expandPmfFactorRows(item)),
  ...asList(productMarketFit.value?.items).flatMap((item) => expandPmfFactorRows(item)),
])
const accountRecommendations = computed(() => [
  ...asList(account360.value?.recommended_accounts),
  ...asList(account360.value?.repeat_or_referral_accounts),
  ...asList(account360.value?.reactivation_accounts),
])
const customerValueRows = computed(() => [
  ...asList(customerValue.value?.commercial_quality_leaders),
  ...asList(customerValue.value?.items),
])
const partnerPerformanceRows = computed(() => [
  ...asList(partnerPerformance.value?.top_investment_candidates),
  ...asList(partnerPerformance.value?.quote_allocation_candidates),
  ...asList(partnerPerformance.value?.pilot_candidates),
  ...asList(partnerPerformance.value?.items),
])
const revenueForecastRows = computed(() => [
  ...asList(revenueForecast.value?.high_probability_projects),
  ...asList(revenueForecast.value?.high_risk_projects),
  ...asList(revenueForecast.value?.committed_backlog),
  ...asList(revenueForecast.value?.forecastable_revenue),
  ...asList(revenueForecast.value?.forecast_items),
])
const partnerOptions = computed(() =>
  uniqueText([
    ...asList(productMarketFit.value?.items).flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...asList(winLossDashboard.value?.partner_rollup).flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...asList(account360.value?.items).flatMap((item) => (Array.isArray(item.partner_focus) ? item.partner_focus : [item.partner_focus])),
    ...partnerPerformanceRows.value.flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...revenueForecastRows.value.flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
  ]),
)
const productOptions = computed(() =>
  uniqueText([
    ...asList(productMarketFit.value?.items).flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_focus, item.product_family, item.product])),
    ...asList(winLossDashboard.value?.product_rollup).flatMap((item) => [item.product_focus, item.product_family, item.product]),
    ...asList(account360.value?.items).flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_focus])),
    ...partnerPerformanceRows.value.flatMap((item) => (Array.isArray(item.product_coverage) ? item.product_coverage : [item.product_focus, item.product_family])),
    ...revenueForecastRows.value.flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_family, item.product_focus])),
  ]),
)
const factorOptions = computed(() =>
  uniqueText([
    ...winLossDecisionFactors.value.flatMap((item) => [item.factor, item.decision_factor, item.reason_category]),
    ...pmfBuyingFactors.value.flatMap((item) => [item.factor, item.dimension, item.buying_factor]),
    ...asList(productMarketFit.value?.items).flatMap((item) => (Array.isArray(item.dimensions) ? item.dimensions : [])),
  ]),
)
const customerOptions = computed(() =>
  uniqueText([
    ...asList(account360.value?.items).flatMap((item) => [item.customer_name, item.account_key]),
    ...asList(winLossDashboard.value?.items).flatMap((item) => [item.customer, item.customer_name]),
    ...customerValueRows.value.flatMap((item) => [item.customer_name, item.account_key]),
    ...revenueForecastRows.value.flatMap((item) => [item.customer_name, item.customer_or_segment, item.account_key]),
  ]),
)
const filteredReasonClusters = computed(() => filterExperienceRows(winLossReasonClusters.value))
const filteredBuyingFactors = computed(() => filterExperienceRows(pmfBuyingFactors.value))
const filteredAccounts = computed(() => filterExperienceRows(accountRecommendations.value))
const filteredDecisionFactors = computed(() => filterExperienceRows(winLossDecisionFactors.value))

const managementSections = computed(() => [
  {
    key: 'follow',
    title: '谁最值得跟进',
    description: '按 Account 360、客户价值和下一商业动作判断。',
    priority: 'P1',
    items: asList(questions.value.who_to_follow_today),
  },
  {
    key: 'convert',
    title: '什么最容易成交',
    description: '按 PMF、订单证据、赢输原因和购买因素判断。',
    priority: 'P1',
    items: asList(questions.value.what_converts),
  },
  {
    key: 'revenue',
    title: '未来收入来自哪里',
    description: '按机会、报价、订单 backlog 的加权预测判断。',
    priority: 'P1',
    items: asList(questions.value.future_revenue_from),
  },
  {
    key: 'partner',
    title: '哪个 Partner 值得投入',
    description: '按报价支持、赢单、订单、交付和反馈判断。',
    priority: 'P2',
    items: asList(questions.value.which_partner_to_invest),
  },
  {
    key: 'winloss',
    title: '为什么赢 / 为什么输',
    description: '把客户决策因素沉淀为下一次报价和 Campaign 的经验。',
    priority: 'P2',
    items: [...asList(questions.value.why_we_win), ...asList(questions.value.why_we_lose)],
  },
  {
    key: 'quality',
    title: '什么是健康商业价值',
    description: '不用成本或利润字段，用成交、复购、pipeline 和服务负担判断。',
    priority: 'P2',
    items: asList(questions.value.what_is_commercially_healthy),
  },
])

const assetSections = computed(() => [
  {
    key: 'account360',
    label: 'Account 360',
    items: asList(commercial.value?.account_360).map((item) => ({
      title: String(item.customer_name || item.account_key || '客户账户'),
      tags: textList([item.current_stage, item.priority, firstText(item.partner_focus), ...(Array.isArray(item.product_focus) ? item.product_focus : [])]),
      reason: String(item.decision_reason || item.repeat_business_signal || '客户商业档案已聚合。'),
      nextAction: String(item.next_action || '查看客户视角完整商业档案。'),
      path: String(item.path || firstText(item.active_paths) || '/growth-operations'),
    })),
  },
  {
    key: 'pmf',
    label: 'Product-Market Fit',
    items: asList(commercial.value?.product_market_fit).map((item) => ({
      title: `${item.partner_focus || 'future partner'} / ${textList(item.product_focus).join(' / ') || 'product family'}`,
      tags: textList([item.fit_status, ...(Array.isArray(item.purchase_factors) ? item.purchase_factors : [])]),
      reason: String(item.commercial_question || '产品市场证据已聚合。'),
      nextAction: String(item.next_action || '复核购买因素、项目经验和客户反馈。'),
      path: String(item.path || item.source_path || '/market-response'),
    })),
  },
  {
    key: 'partner',
    label: 'Partner Performance',
    items: uniqueRows([...partnerPerformanceRows.value, ...asList(commercial.value?.partner_performance)]).map((item) => ({
      title: String(item.partner_name || item.partner_focus || 'Partner'),
      tags: textList([item.investment_priority, item.allocation_fit, item.pilot_fit, ...(Array.isArray(item.product_coverage) ? item.product_coverage : [])]),
      reason: `报价支持 ${item.quote_support_count ?? 0}，赢单率 ${percent(item.win_rate)}，订单额 ${money(item.order_amount)}。`,
      nextAction: String(item.next_allocation_action || item.next_action || '查看 Partner 绩效证据。'),
      path: String(item.path || '/partner-onboarding'),
    })),
  },
  {
    key: 'winloss',
    label: 'Win/Loss',
    items: asList(commercial.value?.win_loss).map((item) => ({
      title: String(item.customer || item.quote_number || item.opportunity_name || '商业经验'),
      tags: textList([item.outcome, item.reason_category, ...(Array.isArray(item.decision_factors) ? item.decision_factors : [])]),
      reason: String(item.commercial_lesson || item.won_reason || item.lost_reason || '成交/丢单原因待补充。'),
      nextAction: String(item.next_quote_guidance || '把经验复用到下一次报价。'),
      path: String(item.path || '/quotes'),
    })),
  },
  {
    key: 'customerValue',
    label: '客户价值',
    items: uniqueRows([...customerValueRows.value, ...asList(commercial.value?.customer_value)]).map((item) => ({
      title: String(item.customer_name || '客户'),
      tags: textList([item.value_tier, item.priority, item.future_revenue_signal, asRecord(item.commercial_quality).tier]),
      reason: `报价 ${money(item.historical_quote_amount)}，成交 ${money(item.won_order_amount)}，pipeline ${money(item.weighted_pipeline_amount)}。`,
      nextAction: String(item.next_action || item.recommended_reason || '按客户价值决定跟进深度。'),
      path: String(item.path || '/companies'),
    })),
  },
  {
    key: 'forecast',
    label: '收入预测',
    items: uniqueRows([
      ...revenueForecastRows.value,
      ...asList(asRecord(commercial.value?.revenue_forecast).high_probability_projects),
    ]).map((item) => ({
      title: String(item.name || item.customer_name || item.source_type || '预测项目'),
      tags: textList([item.source_type, item.risk_level, item.forecast_confidence, item.revenue_bucket]),
      reason: `概率 ${item.probability ?? 0}%，加权金额 ${money(item.weighted_amount)}。`,
      nextAction: String(item.next_action || '保持人工跟进和预测输入更新。'),
      path: String(item.path || '/growth-operations'),
    })),
  },
])

const activeAssetLabel = computed(() => assetSections.value.find((item) => item.key === activeAsset.value)?.label || '商业资产')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [businessExecution, winLoss, pmf, accounts, customers, partners, forecast] = await Promise.all([
      fetchBusinessExecution(),
      fetchWinLossIntelligenceDashboard(120),
      fetchProductMarketFitIntelligence(80),
      fetchAccount360Intelligence(80),
      fetchCustomerValueIntelligence(80),
      fetchPartnerPerformanceIntelligence(80),
      fetchRevenueForecastIntelligence(120),
    ])
    data.value = businessExecution
    winLossDashboard.value = winLoss
    productMarketFit.value = pmf
    account360.value = accounts
    customerValue.value = customers
    partnerPerformance.value = partners
    revenueForecast.value = forecast
  } catch (err) {
    error.value = err instanceof Error ? err.message : '商业智能数据加载失败'
  } finally {
    loading.value = false
  }
}

function go(path: string) {
  router.push(path)
}

async function openAccount360(item: Row) {
  const key = String(item.account_key || (item.company_id ? `company:${item.company_id}` : '')).trim()
  if (!key) {
    accountDetailError.value = 'Account 360 profile key is missing.'
    accountDetail.value = null
    accountDetailVisible.value = true
    return
  }
  accountDetailVisible.value = true
  accountDetailLoading.value = true
  accountDetailError.value = ''
  try {
    accountDetail.value = await fetchAccount360Detail(key)
  } catch (err) {
    accountDetail.value = null
    accountDetailError.value = err instanceof Error ? err.message : 'Account 360 detail failed to load.'
  } finally {
    accountDetailLoading.value = false
  }
}

async function openWinLossFactor(item: Row) {
  const factor = primaryText(item, ['factor', 'decision_factor', 'reason_category', 'product_focus'], '').trim()
  if (!factor) {
    factorDetailError.value = 'Win/Loss factor is missing.'
    factorDetail.value = null
    factorDetailVisible.value = true
    return
  }
  factorDetailVisible.value = true
  factorDetailLoading.value = true
  factorDetailError.value = ''
  try {
    factorDetail.value = await fetchWinLossFactorDetail(factor)
  } catch (err) {
    factorDetail.value = null
    factorDetailError.value = err instanceof Error ? err.message : 'Win/Loss factor detail failed to load.'
  } finally {
    factorDetailLoading.value = false
  }
}

async function openProductMarketFitFactor(item: Row) {
  const factor = primaryText(item, ['factor', 'dimension', 'buying_factor', 'product_focus'], '').trim()
  if (!factor) {
    pmfDetailError.value = 'Product-Market Fit factor is missing.'
    pmfDetail.value = null
    pmfDetailVisible.value = true
    return
  }
  pmfDetailVisible.value = true
  pmfDetailLoading.value = true
  pmfDetailError.value = ''
  try {
    pmfDetail.value = await fetchProductMarketFitFactorDetail(factor)
  } catch (err) {
    pmfDetail.value = null
    pmfDetailError.value = err instanceof Error ? err.message : 'Product-Market Fit factor detail failed to load.'
  } finally {
    pmfDetailLoading.value = false
  }
}

function expandPmfFactorRows(item: Row) {
  const rows = asList(item.buying_factors_ranked || item.buying_factors)
  if (!rows.length) return [item]
  return rows.map((row) => ({
    ...item,
    ...row,
    partner_focus: row.partner_focus || item.partner_focus,
    product_focus: row.product_focus || item.product_focus,
    next_action: row.next_action || item.next_action,
    path: row.path || item.path,
  }))
}

function asRecord(value: unknown): Row {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as Row) : {}
}

function asList(value: unknown): Row[] {
  return Array.isArray(value) ? (value.filter((item) => item && typeof item === 'object') as Row[]) : []
}

function firstText(value: unknown) {
  if (Array.isArray(value)) return value.length ? String(value[0]) : ''
  return value ? String(value) : ''
}

function primaryText(row: Row, keys: string[], fallback: string) {
  for (const key of keys) {
    const value = row[key]
    if (Array.isArray(value) && value.length) return value.map((item) => String(item)).join(' / ')
    if (value !== null && value !== undefined && String(value).trim()) return String(value)
  }
  return fallback
}

function textList(value: unknown) {
  const values = Array.isArray(value) ? value : [value]
  return values.filter((item) => item !== null && item !== undefined && String(item).trim()).map((item) => String(item))
}

function uniqueText(values: unknown[]) {
  return [...new Set(textList(values))].sort((left, right) => left.localeCompare(right))
}

function uniqueRows(rows: Row[]) {
  const seen = new Set<string>()
  return rows.filter((row) => {
    const key = rowKey(row)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function rowSearchText(row: Row) {
  return JSON.stringify(row).toLowerCase()
}

function includesFilter(row: Row, filter: string) {
  return !filter || rowSearchText(row).includes(filter.toLowerCase())
}

function filterExperienceRows(rows: Row[]) {
  return rows.filter(
    (row) =>
      includesFilter(row, selectedPartner.value) &&
      includesFilter(row, selectedProduct.value) &&
      includesFilter(row, selectedFactor.value) &&
      includesFilter(row, selectedCustomer.value),
  )
}

function nextMotion(item: Row) {
  return asRecord(item.next_commercial_motion)
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

function rowKey(row: Row) {
  return String(row.path || row.title || row.customer_name || row.name || row.partner_name || JSON.stringify(row).slice(0, 80))
}

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  if (priority === 'P2') return 'primary'
  return 'info'
}

onMounted(load)
</script>
