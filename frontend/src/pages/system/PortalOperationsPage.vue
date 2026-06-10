<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Portal 运营</h2>
        <p class="mt-1 text-sm text-slate-600">客户可见 Portal 数据的内部联调与运营控制台。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="只读运营视图。本页不会通知客户或供应商，不调用承运商 API，也不会修改订单状态。"
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">客户 Portal 运营价值</h3>
          <p class="mt-1 text-sm text-slate-600">
            本控制台展示 PartnerOS 内部运营到客户 Portal 的桥接：产品可见性、订单状态、生产进度、物流计划、资料中心和反馈入口。
          </p>
        </div>
        <el-tag type="info" effect="plain">READY_FOR_STAGING_HANDOFF</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">产品</p>
          <p class="mt-1 text-sm text-slate-700">客户安全字段决定 Portal 能展示哪些产品信息。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">订单</p>
          <p class="mt-1 text-sm text-slate-700">近期可见订单构成客户账号时间线。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">生产</p>
          <p class="mt-1 text-sm text-slate-700">里程碑转化为客户进度，不暴露供应商私有备注。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">物流</p>
          <p class="mt-1 text-sm text-slate-700">人工维护物流计划，在就绪后展示 ETD、ETA 和追踪信息。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">反馈</p>
          <p class="mt-1 text-sm text-slate-700">Portal 反馈进入内部队列，不自动回复。</p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">上线准备度</h3>
        <el-tag :type="data?.portal_launch_readiness.ready_for_real_staging ? 'success' : 'warning'">
          {{ data?.portal_launch_readiness.ready_for_real_staging ? '可联调' : '需处理' }}
        </el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="(ready, check) in data?.portal_launch_readiness.checks || {}" :key="check" class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">{{ check }}</p>
          <el-tag class="mt-2" size="small" :type="ready ? 'success' : 'warning'" effect="plain">{{ ready ? '通过' : '检查' }}</el-tag>
        </div>
      </div>
      <div v-if="data?.portal_launch_readiness.blockers.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="blocker in data.portal_launch_readiness.blockers" :key="blocker" type="danger" effect="plain">{{ blocker }}</el-tag>
      </div>
      <div v-if="data?.portal_launch_readiness.warnings.length" class="mt-2 flex flex-wrap gap-2">
        <el-tag v-for="warning in data.portal_launch_readiness.warnings" :key="warning" type="warning" effect="plain">{{ warning }}</el-tag>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Staging 联调 checklist</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag :type="data?.staging_integration_checklist.ready_for_staging_operator ? 'success' : 'warning'" effect="plain">
            {{ data?.staging_integration_checklist.ready_for_staging_operator ? '运营可接手' : '存在阻塞' }}
          </el-tag>
          <el-tag :type="data?.staging_integration_checklist.safety.staging_validated ? 'danger' : 'info'" effect="plain">
            {{ data?.staging_integration_checklist.safety.staging_validated ? '已验证' : '仅 handoff' }}
          </el-tag>
        </div>
      </div>
      <div class="mb-3 grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">已完成</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.staging_integration_checklist.done_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">运营动作</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.staging_integration_checklist.operator_action_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">阻塞</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.staging_integration_checklist.blocked_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Proof records</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.staging_integration_checklist.safety.proof_record_created ? '已创建' : '无' }}</p>
        </div>
      </div>
      <el-table :data="data?.staging_integration_checklist.items || []" class="w-full">
        <el-table-column prop="label" label="项目" min-width="190" />
        <el-table-column label="状态" width="160">
          <template #default="{ row }">
            <el-tag size="small" :type="checklistStatusType(row.status)" effect="plain">{{ checklistStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="动作" min-width="360" />
        <el-table-column prop="detail" label="说明" min-width="230" />
        <el-table-column label="安全" width="155">
          <template #default="{ row }">
            <el-tag size="small" :type="row.safety.proof_record_created || row.safety.token_value_exposed ? 'danger' : 'success'" effect="plain">
              {{ row.safety.proof_record_created || row.safety.token_value_exposed ? '检查' : '安全' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Portal API</p>
        <el-tag class="mt-2" :type="data?.status.enabled ? 'success' : 'danger'">
          {{ data?.status.enabled ? '已启用' : '未启用' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Token</p>
        <el-tag class="mt-2" :type="data?.status.token_configured ? 'success' : 'warning'">
          {{ data?.status.token_configured ? '已配置' : '缺失' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Public base URL</p>
        <el-tag class="mt-2" :type="data?.status.public_base_url_configured ? 'success' : 'warning'">
          {{ data?.status.public_base_url_configured ? '已配置' : '缺失' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">禁用字段审计</p>
        <el-tag class="mt-2" :type="data?.forbidden_field_audit.hits.length ? 'danger' : 'success'">
          {{ data?.forbidden_field_audit.hits.length ? `${data.forbidden_field_audit.hits.length} 个命中` : '通过' }}
        </el-tag>
        <p class="mt-2 text-xs text-slate-500">
          {{ data?.forbidden_field_audit.checked_payloads?.join(', ') || '未检查' }}
        </p>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">运行健康</h3>
        <el-tag :type="data?.runtime_health.ok ? 'success' : 'warning'">{{ data?.runtime_health.ok ? '健康' : '需检查' }}</el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">数据库</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.database_status || '-' }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Migration</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.migration_pending ? '待升级' : '已到 head' }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Portal API</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.portal_customer_api_ready ? '就绪' : '需配置' }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Alembic</p>
          <p class="mt-1 text-xs text-slate-600">{{ data?.runtime_health.alembic_current_revision || '-' }}</p>
        </div>
      </div>
      <div v-if="data?.runtime_health.warnings.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="warning in data.runtime_health.warnings" :key="warning" type="warning" effect="plain">{{ warning }}</el-tag>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">接口准备度</h3>
        <el-tag :type="data?.status.ready ? 'success' : 'warning'">{{ data?.status.ready ? '就绪' : '需配置' }}</el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="(ready, name) in data?.endpoint_readiness || {}" :key="name" class="rounded border border-slate-200 p-3">
          <p class="text-sm capitalize text-slate-600">{{ name }}</p>
          <el-tag class="mt-2" size="small" :type="ready ? 'success' : 'danger'">{{ ready ? '就绪' : '未就绪' }}</el-tag>
        </div>
      </div>
      <div v-if="data?.status.missing_config.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="item in data.status.missing_config" :key="item" type="warning" effect="plain">{{ item }}</el-tag>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[0.9fr_1.4fr]">
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Staging 连接</h3>
        <dl class="space-y-3 text-sm">
          <div>
            <dt class="text-slate-500">Public base URL</dt>
            <dd class="break-all font-medium text-slate-800">{{ data?.portal_contract.base_url || '-' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Auth header</dt>
            <dd class="font-medium text-slate-800">{{ data?.portal_contract.server_to_server_auth.header_name || '-' }}</dd>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-tag :type="data?.portal_contract.server_to_server_auth.required ? 'success' : 'warning'" effect="plain">
              {{ data?.portal_contract.server_to_server_auth.required ? '需要 token' : 'token 可选' }}
            </el-tag>
            <el-tag :type="data?.portal_contract.server_to_server_auth.token_configured ? 'success' : 'warning'" effect="plain">
              {{ data?.portal_contract.server_to_server_auth.token_configured ? 'token 已配置' : 'token 缺失' }}
            </el-tag>
            <el-tag :type="data?.portal_contract.safety.token_value_exposed ? 'danger' : 'success'" effect="plain">
              {{ data?.portal_contract.safety.token_value_exposed ? 'token 暴露' : 'token 隐藏' }}
            </el-tag>
          </div>
          <div>
            <dt class="text-slate-500">Allowed origins</dt>
            <dd class="mt-1 flex flex-wrap gap-2">
              <el-tag v-for="origin in data?.portal_contract.allowed_origins || []" :key="origin" effect="plain">{{ origin }}</el-tag>
              <span v-if="!data?.portal_contract.allowed_origins.length" class="text-slate-500">-</span>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">Required env</dt>
            <dd class="mt-1 grid gap-2">
              <div
                v-for="item in data?.portal_contract.connection_guide.required_environment || []"
                :key="item.name"
                class="flex items-center justify-between gap-2 rounded border border-slate-200 px-2 py-1"
              >
                <span class="font-medium text-slate-700">{{ item.name }}</span>
                <el-tag size="small" :type="item.configured ? 'success' : 'warning'" effect="plain">
                  {{ item.configured ? '已配置' : '缺失' }}
                </el-tag>
              </div>
            </dd>
          </div>
        </dl>
      </div>

      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Portal 契约</h3>
        <el-table :data="data?.portal_contract.endpoints || []" class="w-full">
          <el-table-column prop="method" label="方法" width="90" />
          <el-table-column prop="name" label="数据" width="140" />
          <el-table-column prop="path" label="Path" min-width="310" />
          <el-table-column label="就绪" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.ready ? 'success' : 'warning'">{{ row.ready ? '就绪' : '检查' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">Service Portal 冒烟顺序</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag
            :type="data?.portal_contract.connection_guide.safety.browser_token_storage_allowed ? 'danger' : 'success'"
            effect="plain"
          >
            {{ data?.portal_contract.connection_guide.safety.browser_token_storage_allowed ? '浏览器 token 风险' : '服务端 token' }}
          </el-tag>
          <el-tag
            :type="data?.portal_contract.connection_guide.safety.staging_validated ? 'danger' : 'info'"
            effect="plain"
          >
            {{ data?.portal_contract.connection_guide.safety.staging_validated ? '已验证' : '仅 handoff' }}
          </el-tag>
        </div>
      </div>
      <el-table :data="data?.portal_contract.connection_guide.smoke_sequence || []" class="w-full">
        <el-table-column prop="method" label="方法" width="95" />
        <el-table-column prop="key" label="步骤" width="145" />
        <el-table-column prop="path" label="Path" min-width="330" />
        <el-table-column label="订单来源" min-width="180">
          <template #default="{ row }">{{ row.uses_order_id_from || '-' }}</template>
        </el-table-column>
        <el-table-column label="预期" width="105">
          <template #default="{ row }">HTTP {{ row.expected_status }}</template>
        </el-table-column>
        <el-table-column label="安全" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.mutates_data ? 'warning' : 'success'" effect="plain">
              {{ row.mutates_data ? '测试工单' : '只读' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">客户字段契约</h3>
        <el-tag :type="data?.portal_contract.field_contract.date_policy.planned_dates_are_guarantees ? 'danger' : 'success'" effect="plain">
          {{ data?.portal_contract.field_contract.date_policy.planned_dates_are_guarantees ? '日期承诺风险' : '仅计划日期' }}
        </el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Product fields</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.portal_contract.field_contract.products.length ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Order fields</p>
          <p class="mt-1 font-medium text-slate-800">
            {{ (data?.portal_contract.field_contract.order_summary.length ?? 0) + (data?.portal_contract.field_contract.order_detail.length ?? 0) }}
          </p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Snapshot stages</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.portal_contract.field_contract.customer_status_stages.length ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Feedback request fields</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.portal_contract.field_contract.feedback_create.length ?? 0 }}</p>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="stage in data?.portal_contract.field_contract.customer_status_stages || []" :key="stage" effect="plain">
          {{ stage }}
        </el-tag>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Feedback types</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <el-tag
              v-for="type in data?.portal_contract.field_contract.feedback_form_contract.allowed_feedback_types || []"
              :key="type"
              size="small"
              effect="plain"
            >
              {{ type }}
            </el-tag>
          </div>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Feedback priorities</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <el-tag
              v-for="priority in data?.portal_contract.field_contract.feedback_form_contract.allowed_priorities || []"
              :key="priority"
              size="small"
              effect="plain"
            >
              {{ priority }}
            </el-tag>
            <el-tag
              size="small"
              :type="data?.portal_contract.field_contract.feedback_form_contract.resolution_time_promised ? 'danger' : 'success'"
              effect="plain"
            >
              {{ data?.portal_contract.field_contract.feedback_form_contract.resolution_time_promised ? 'SLA promised' : 'no SLA promise' }}
            </el-tag>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">近期客户可见订单</h3>
        <el-table :data="data?.recent_customer_visible_orders.items || []" v-loading="loading" class="w-full">
          <el-table-column label="订单" width="165">
            <template #default="{ row }">
              <el-button link type="primary" @click="openOrder(row.id)">{{ row.order_number }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="company_name" label="客户" min-width="180" />
          <el-table-column label="状态" width="170">
            <template #default="{ row }">{{ zhLabel(ORDER_STATUS_LABELS, row.status) }}</template>
          </el-table-column>
          <el-table-column label="Portal 阶段" min-width="170">
            <template #default="{ row }">
              <div class="font-medium text-slate-800">{{ row.portal_tracking.label || '-' }}</div>
              <div class="text-xs text-slate-500">{{ row.portal_tracking.stage || '客户快照待生成' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="信号" min-width="220">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-if="row.portal_tracking.has_production_updates" size="small" effect="plain">生产</el-tag>
                <el-tag v-if="row.portal_tracking.has_active_shipment" size="small" effect="plain">物流 {{ row.portal_tracking.active_shipment_count }}</el-tag>
                <el-tag v-if="row.portal_tracking.has_visible_resources" size="small" effect="plain">资料</el-tag>
                <el-button
                  v-if="row.portal_tracking.has_open_feedback"
                  size="small"
                  type="warning"
                  plain
                  @click.stop="openOrderFeedback(row.id)"
                >
                  反馈 {{ row.portal_tracking.open_feedback_count }}
                </el-button>
                <span
                  v-if="
                    !row.portal_tracking.has_production_updates &&
                    !row.portal_tracking.has_active_shipment &&
                    !row.portal_tracking.has_visible_resources &&
                    !row.portal_tracking.has_open_feedback
                  "
                  class="text-sm text-slate-500"
                >
                  暂无
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="150">
            <template #default="{ row }">{{ row.grand_total || '-' }} {{ row.currency }}</template>
          </el-table-column>
          <el-table-column label="UAT" width="105">
            <template #default="{ row }">
              <el-button size="small" @click="openPortalBridge(row.id)">检查</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">物流状态</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in data?.shipment_status_counts || {}" :key="status" effect="plain">
            {{ zhLabel(SHIPMENT_STATUS_LABELS, String(status)) }} {{ count }}
          </el-tag>
          <span v-if="!Object.keys(data?.shipment_status_counts || {}).length" class="text-sm text-slate-500">暂无物流计划</span>
        </div>
        <div class="mt-4 grid gap-2 sm:grid-cols-2">
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">活跃计划</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.shipment_readiness.active_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">待补日期</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.shipment_readiness.missing_estimated_dates_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">已发运但缺追踪</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.shipment_readiness.shipped_without_tracking_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">Portal 就绪</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.shipment_readiness.ready ? '是' : '需检查' }}</p>
          </div>
        </div>
        <el-table v-if="data?.shipment_readiness.action_items.length" :data="data.shipment_readiness.action_items" class="mt-4 w-full">
          <el-table-column label="状态" width="110">
            <template #default="{ row }">{{ zhLabel(SHIPMENT_STATUS_LABELS, row.status) }}</template>
          </el-table-column>
          <el-table-column prop="shipment_method" label="方式" width="120" />
          <el-table-column prop="estimated_ship_date" label="发运日期" width="130" />
          <el-table-column prop="estimated_arrival_date" label="到港日期" width="130" />
          <el-table-column prop="action" label="动作" min-width="230" />
          <el-table-column label="订单" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="openOrder(row.order_id)">打开</el-button>
            </template>
          </el-table-column>
          <el-table-column label="安全" width="145">
            <template #default="{ row }">
              <el-tag size="small" :type="row.safety.carrier_api_called || row.safety.shipment_created ? 'danger' : 'success'" effect="plain">
                {{ row.safety.carrier_api_called || row.safety.shipment_created ? '检查' : '只读' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <h3 class="mb-3 mt-5 font-semibold text-slate-800">反馈状态</h3>
        <div class="flex flex-wrap items-center gap-2">
          <el-button
            v-for="(count, status) in data?.feedback_status_counts || {}"
            :key="status"
            size="small"
            @click="openFeedbackQueue({ status: String(status) })"
          >
            {{ zhLabel(FEEDBACK_STATUS_LABELS, String(status)) }} {{ count }}
          </el-button>
          <span v-if="!Object.keys(data?.feedback_status_counts || {}).length" class="text-sm text-slate-500">暂无工单</span>
        </div>
        <div class="mt-2 flex flex-wrap gap-2">
          <el-button size="small" @click="openFeedbackQueue({ operation_filter: 'needs_internal_review' })">需复核</el-button>
          <el-button size="small" @click="openFeedbackQueue({ priority: 'urgent' })">紧急</el-button>
          <el-button size="small" @click="openFeedbackQueue({ priority: 'high' })">高优先级</el-button>
          <el-button size="small" @click="openFeedbackQueue({ operation_filter: 'ready_to_close' })">可关闭</el-button>
        </div>
        <div class="mt-4 grid gap-2 sm:grid-cols-2">
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">需复核</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.needs_internal_review_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">高优先级</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.high_priority_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">可关闭</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.ready_to_close_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">最早未结</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.oldest_open_age_days ?? '-' }}</p>
          </div>
        </div>
        <el-table v-if="data?.feedback_operations.action_items.length" :data="data.feedback_operations.action_items" class="mt-4 w-full">
          <el-table-column label="工单" width="145">
            <template #default="{ row }">
              <el-button link type="primary" @click="openFeedbackTicket(row.id)">{{ row.ticket_number }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="subject" label="主题" min-width="190" />
          <el-table-column prop="priority" label="优先级" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.priority === 'urgent' ? 'danger' : row.priority === 'high' ? 'warning' : 'info'" effect="plain">
                {{ zhLabel(FEEDBACK_PRIORITY_LABELS, row.priority) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="动作" min-width="210">
            <template #default="{ row }">{{ row.action_label || row.action }}</template>
          </el-table-column>
          <el-table-column label="处理" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="openFeedbackAction(row)">打开</el-button>
            </template>
          </el-table-column>
          <el-table-column label="安全" width="150">
            <template #default="{ row }">
              <el-tag size="small" :type="row.safety.customer_notified || row.safety.automatic_reply_sent ? 'danger' : 'success'" effect="plain">
                {{ row.safety.customer_notified || row.safety.automatic_reply_sent ? '检查' : '仅内部' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">多 Partner 运营闭环准备度</h3>
        <el-tag :type="data?.multi_partner_flow_readiness.safety.partner_neutral ? 'success' : 'danger'" effect="plain">
          {{ data?.multi_partner_flow_readiness.safety.partner_neutral ? 'partner neutral' : 'check partner policy' }}
        </el-tag>
      </div>
      <div class="mb-4 grid gap-2 md:grid-cols-4 xl:grid-cols-7">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Partners</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partner_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Orders</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.order_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Splits</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.split_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">With production</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partners_with_production ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">已有物流</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partners_with_shipments ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">存在风险</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partners_with_risk ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">是否排序</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.safety.partner_ranked ? '是' : '否' }}</p>
        </div>
      </div>
      <el-table :data="data?.multi_partner_flow_readiness.items || []" class="w-full">
        <el-table-column prop="partner_name" label="Partner" min-width="180" />
        <el-table-column prop="partner_type" label="类型" width="140" />
        <el-table-column prop="order_count" label="订单" width="100" />
        <el-table-column prop="split_count" label="拆分" width="100" />
        <el-table-column prop="line_item_count" label="行项目" width="100" />
        <el-table-column prop="active_shipment_count" label="物流" width="120" />
        <el-table-column label="风险" min-width="220">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-for="flag in row.risk_flags" :key="flag" size="small" type="warning" effect="plain">{{ flag }}</el-tag>
              <span v-if="!row.risk_flags.length" class="text-sm text-slate-500">无明显风险</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">客户可见快照</h3>
        <el-tag :type="data?.customer_snapshot_readiness.portal_ready ? 'success' : 'warning'" effect="plain">
          {{ data?.customer_snapshot_readiness.portal_ready ? 'Portal 就绪' : '待补数据' }}
        </el-tag>
        <el-tag :type="data?.snapshot_coverage.coverage_complete ? 'success' : 'warning'" effect="plain">
          {{ data?.snapshot_coverage.coverage_complete ? '近期已覆盖' : '覆盖缺口' }}
        </el-tag>
      </div>
      <div class="mb-4 grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">快照</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.snapshot_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">生产可见</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.production_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">活跃物流</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.active_shipment_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">未结反馈</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.open_feedback_count ?? 0 }}</p>
        </div>
      </div>
      <div class="mb-4 grid gap-2 md:grid-cols-3">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">近期订单</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.snapshot_coverage.recent_order_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">快照覆盖</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.snapshot_coverage.snapshot_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">缺失快照</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.snapshot_coverage.missing_snapshot_count ?? 0 }}</p>
        </div>
      </div>
      <div class="mb-4 flex flex-wrap gap-2">
        <el-tag v-for="(count, stage) in data?.customer_snapshot_readiness.stage_counts || {}" :key="stage" effect="plain">
          {{ stage }} {{ count }}
        </el-tag>
        <el-tag v-if="data?.customer_snapshot_readiness.missing_progress_count" type="warning" effect="plain">
          缺少进度 {{ data.customer_snapshot_readiness.missing_progress_count }}
        </el-tag>
      </div>
      <el-table v-if="data?.customer_snapshot_readiness.action_items.length" :data="data.customer_snapshot_readiness.action_items" class="mb-4 w-full">
        <el-table-column label="订单" width="150">
          <template #default="{ row }">
            <el-button v-if="row.order_id" link type="primary" @click="openOrder(row.order_id)">{{ row.order_number }}</el-button>
            <span v-else>{{ row.order_number || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="label" label="阶段" min-width="170" />
        <el-table-column prop="next_action_label" label="Portal 下一步" min-width="190" />
        <el-table-column prop="action" label="内部动作" min-width="250" />
        <el-table-column label="信号" width="170">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-if="row.active_shipment_count" size="small" effect="plain">物流 {{ row.active_shipment_count }}</el-tag>
              <el-button
                v-if="row.open_feedback_count"
                size="small"
                type="warning"
                plain
                @click="openOrderFeedback(row.order_id)"
              >
                反馈 {{ row.open_feedback_count }}
              </el-button>
              <span v-if="!row.active_shipment_count && !row.open_feedback_count" class="text-sm text-slate-500">暂无</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="安全" width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="row.safety.read_only && !row.safety.order_status_mutated ? 'success' : 'danger'" effect="plain">
              {{ row.safety.read_only && !row.safety.order_status_mutated ? '只读' : '检查' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-table v-if="data?.snapshot_coverage.action_items.length" :data="data.snapshot_coverage.action_items" class="mb-4 w-full">
        <el-table-column label="订单" width="150">
          <template #default="{ row }">
            <el-button v-if="row.order_id" link type="primary" @click="openOrder(row.order_id)">{{ row.order_number }}</el-button>
            <span v-else>{{ row.order_number || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="150" />
        <el-table-column prop="action" label="覆盖动作" min-width="250" />
        <el-table-column label="安全" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.safety.read_only && !row.safety.customer_notified ? 'success' : 'danger'" effect="plain">
              {{ row.safety.read_only && !row.safety.customer_notified ? '只读' : '检查' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-table :data="data?.customer_snapshots || []" class="w-full">
        <el-table-column label="订单" width="170">
          <template #default="{ row }">
            <el-button link type="primary" @click="openOrder(row.order.id)">{{ row.order.order_number }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="客户阶段" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.portal_display?.headline || row.customer_status.label }}</div>
            <div class="text-xs text-slate-500">{{ row.portal_display?.current_step_label || row.customer_status.stage }}</div>
          </template>
        </el-table-column>
        <el-table-column label="下一步" min-width="240">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.customer_status.next_action_label }}</div>
            <div class="text-xs text-slate-500">{{ row.customer_status.next_action_detail }}</div>
          </template>
        </el-table-column>
        <el-table-column label="进度" min-width="260">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag
                v-for="badge in row.portal_display?.status_badges || row.customer_status.progress_steps"
                :key="badge.key"
                size="small"
                :type="badge.state === 'current' ? 'warning' : badge.state === 'complete' ? 'success' : 'info'"
                effect="plain"
              >
                {{ badge.label }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="物流" width="160">
          <template #default="{ row }">活跃 {{ row.shipment.active_count }}</template>
        </el-table-column>
        <el-table-column label="时间线" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.customer_timeline?.has_attention ? 'warning' : 'success'" effect="plain">
              {{ row.customer_timeline?.total ?? 0 }} 条事件
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="信号" min-width="210">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <template v-for="card in row.portal_display?.signal_cards || []" :key="card.key">
                <el-button
                  v-if="card.active && card.key === 'feedback'"
                  size="small"
                  type="warning"
                  plain
                  @click="openOrderFeedback(row.order.id)"
                >
                  {{ card.label }} {{ card.count }}
                </el-button>
                <el-tag v-else-if="card.active" size="small" type="info" effect="plain">
                  {{ card.label }} {{ card.count }}
                </el-tag>
              </template>
              <span
                v-if="
                  !row.tracking_summary.has_production_updates &&
                  !row.tracking_summary.has_active_shipment &&
                  !row.tracking_summary.has_visible_resources &&
                  !row.tracking_summary.has_open_feedback
                "
                class="text-sm text-slate-500"
              >
                暂无
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="未结反馈" width="150">
          <template #default="{ row }">{{ row.feedback.open_count }}</template>
        </el-table-column>
        <el-table-column label="UAT" width="105">
          <template #default="{ row }">
            <el-button size="small" @click="openPortalBridge(row.order.id)">检查</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">资料中心准备度</h3>
        <el-tag :type="data?.resource_readiness.ready ? 'success' : 'warning'" effect="plain">
          {{ data?.resource_readiness.ready ? '已有可见资料' : '暂无可见资料' }}
        </el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Portal 可见</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.portal_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">客户可见</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.customer_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">待发布</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.blocked_visibility_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">已发布但隐藏</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.hidden_published_count ?? 0 }}</p>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="(count, status) in data?.resource_readiness.status_counts || {}" :key="status" effect="plain">
          {{ zhLabel(RESOURCE_STATUS_LABELS, String(status)) }} {{ count }}
        </el-tag>
        <el-tag :type="data?.resource_readiness.safety.download_links_signed ? 'success' : 'danger'" effect="plain">
          {{ data?.resource_readiness.safety.download_links_signed ? '签名下载' : '未签名下载' }}
        </el-tag>
        <el-tag :type="data?.resource_readiness.safety.file_location_exposed ? 'danger' : 'success'" effect="plain">
          {{ data?.resource_readiness.safety.file_location_exposed ? '文件路径暴露' : '路径隐藏' }}
        </el-tag>
      </div>
      <el-table v-if="data?.resource_readiness.action_items.length" :data="data.resource_readiness.action_items" class="mt-4 w-full">
        <el-table-column prop="title" label="资料" min-width="190" />
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">{{ zhLabel(RESOURCE_STATUS_LABELS, row.status) }}</template>
        </el-table-column>
        <el-table-column label="可见性" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.portal_visible ? 'success' : 'warning'" effect="plain">
              {{ row.portal_visible ? 'Portal 可见' : '不可见' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="动作" min-width="220" />
        <el-table-column label="安全" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.safety.metadata_only && !row.safety.file_location_exposed ? 'success' : 'danger'" effect="plain">
              {{ row.safety.metadata_only && !row.safety.file_location_exposed ? '仅元数据' : '检查' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">市场响应信号</h3>
        <el-tag type="info" effect="plain">仅供运营判断</el-tag>
      </div>
      <el-table :data="data?.market_signal_preview.items || []" class="w-full">
        <el-table-column prop="label" label="关注对象" min-width="190" />
        <el-table-column prop="signal_score" label="分数" width="90" />
        <el-table-column label="主要信号" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.review_label }}</div>
            <div class="text-xs text-slate-500">{{ zhLabel(MARKET_SIGNAL_LABELS, row.primary_signal, row.primary_signal) }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="order_line_count" label="订单行" width="120" />
        <el-table-column prop="ordered_quantity" label="数量" width="100" />
        <el-table-column prop="feedback_count" label="反馈" width="110" />
        <el-table-column prop="delayed_or_blocked_production_count" label="生产风险" width="150" />
        <el-table-column prop="shipment_issue_count" label="物流风险" width="140" />
        <el-table-column label="复核" width="110">
          <template #default="{ row }">
            <el-button size="small" @click="openMarketSignal(row)">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">近期反馈工单</h3>
      <el-table :data="data?.recent_feedback_tickets || []" class="w-full">
        <el-table-column label="工单" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="openFeedbackTicket(row.id)">{{ row.ticket_number }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="subject" label="主题" min-width="220" />
        <el-table-column prop="feedback_type" label="类型" width="130" />
        <el-table-column label="状态" width="130">
          <template #default="{ row }">{{ zhLabel(FEEDBACK_STATUS_LABELS, row.status) }}</template>
        </el-table-column>
        <el-table-column label="优先级" width="120">
          <template #default="{ row }">{{ zhLabel(FEEDBACK_PRIORITY_LABELS, row.priority) }}</template>
        </el-table-column>
        <el-table-column prop="internal_owner" label="负责人" width="150" />
        <el-table-column label="复核" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="row.operation.needs_internal_review ? 'warning' : 'success'" effect="plain">
              {{ row.operation.needs_internal_review ? '需复核' : '通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="天数" width="90">
          <template #default="{ row }">{{ row.operation.age_days ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="处理" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="openFeedbackTicket(row.id)">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { formatApiError } from '@/api/errors'
import { fetchPortalOperationsConsole, type PortalOperationsConsole } from '@/api/portalOperations'
import {
  FEEDBACK_PRIORITY_LABELS,
  FEEDBACK_STATUS_LABELS,
  MARKET_SIGNAL_LABELS,
  ORDER_STATUS_LABELS,
  RESOURCE_STATUS_LABELS,
  SHIPMENT_STATUS_LABELS,
  zhLabel,
} from '@/copy/zhCN'

const data = ref<PortalOperationsConsole | null>(null)
const loading = ref(false)
const error = ref('')
const router = useRouter()

const CHECKLIST_STATUS_LABELS: Record<string, string> = {
  done: '已完成',
  ready_for_operator: '运营可接手',
  needs_operator_action: '需要运营动作',
  blocked: '阻塞',
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPortalOperationsConsole()
  } catch (e) {
    error.value = formatApiError(e, 'Portal 运营控制台加载失败。')
  } finally {
    loading.value = false
  }
}

onMounted(load)

function checklistStatusType(status: string) {
  if (status === 'done' || status === 'ready_for_operator') return 'success'
  if (status === 'needs_operator_action') return 'warning'
  return 'danger'
}

function checklistStatusLabel(status: string) {
  return CHECKLIST_STATUS_LABELS[status] || status
}

function openFeedbackTicket(ticketId: string) {
  router.push({ name: 'feedback-tickets', query: { ticket_id: ticketId } })
}

function openFeedbackQueue(query: Record<string, string | null | undefined>) {
  const cleanQuery = Object.fromEntries(Object.entries(query).filter(([, value]) => value))
  router.push({ name: 'feedback-tickets', query: cleanQuery })
}

function openFeedbackAction(row: { id: string; route_query?: Record<string, string | null | undefined> }) {
  openFeedbackQueue(row.route_query || { ticket_id: row.id })
}

function openOrderFeedback(orderId: string | null | undefined) {
  if (!orderId) return
  openFeedbackQueue({ order_id: orderId })
}

function openOrder(orderId: string) {
  router.push({ name: 'order-detail', params: { orderId } })
}

function openPortalBridge(orderId: string) {
  router.push({ name: 'portal-customer-bridge', query: { order_id: orderId } })
}

function openMarketFocus(focusCategory: string) {
  router.push({ name: 'market', query: { focus_category: focusCategory } })
}

function openMarketSignal(row: { key: string; route_query?: Record<string, string | null | undefined> }) {
  const focusCategory = row.route_query?.focus_category || row.key
  openMarketFocus(focusCategory)
}
</script>
