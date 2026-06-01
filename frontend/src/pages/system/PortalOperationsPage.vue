<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Portal Operations</h2>
        <p class="mt-1 text-sm text-slate-600">Internal launch console for customer-visible Portal data.</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="Read-only operations view. No customer notification, supplier notification, carrier API call, or order status mutation is performed."
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Launch readiness</h3>
        <el-tag :type="data?.portal_launch_readiness.ready_for_real_staging ? 'success' : 'warning'">
          {{ data?.portal_launch_readiness.ready_for_real_staging ? 'ready to connect' : 'needs attention' }}
        </el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="(ready, check) in data?.portal_launch_readiness.checks || {}" :key="check" class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">{{ check }}</p>
          <el-tag class="mt-2" size="small" :type="ready ? 'success' : 'warning'" effect="plain">{{ ready ? 'ok' : 'check' }}</el-tag>
        </div>
      </div>
      <div v-if="data?.portal_launch_readiness.blockers.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="blocker in data.portal_launch_readiness.blockers" :key="blocker" type="danger" effect="plain">{{ blocker }}</el-tag>
      </div>
      <div v-if="data?.portal_launch_readiness.warnings.length" class="mt-2 flex flex-wrap gap-2">
        <el-tag v-for="warning in data.portal_launch_readiness.warnings" :key="warning" type="warning" effect="plain">{{ warning }}</el-tag>
      </div>
    </section>

    <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Portal API</p>
        <el-tag class="mt-2" :type="data?.status.enabled ? 'success' : 'danger'">
          {{ data?.status.enabled ? 'enabled' : 'disabled' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Token</p>
        <el-tag class="mt-2" :type="data?.status.token_configured ? 'success' : 'warning'">
          {{ data?.status.token_configured ? 'configured' : 'missing' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Public base URL</p>
        <el-tag class="mt-2" :type="data?.status.public_base_url_configured ? 'success' : 'warning'">
          {{ data?.status.public_base_url_configured ? 'configured' : 'missing' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Forbidden field audit</p>
        <el-tag class="mt-2" :type="data?.forbidden_field_audit.hits.length ? 'danger' : 'success'">
          {{ data?.forbidden_field_audit.hits.length ? `${data.forbidden_field_audit.hits.length} hit(s)` : 'clear' }}
        </el-tag>
        <p class="mt-2 text-xs text-slate-500">
          {{ data?.forbidden_field_audit.checked_payloads?.join(', ') || 'not checked' }}
        </p>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Runtime health</h3>
        <el-tag :type="data?.runtime_health.ok ? 'success' : 'warning'">{{ data?.runtime_health.ok ? 'healthy' : 'check' }}</el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Database</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.database_status || '-' }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Migration</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.migration_pending ? 'pending' : 'at head' }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Portal API</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.runtime_health.portal_customer_api_ready ? 'ready' : 'needs config' }}</p>
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
        <h3 class="font-semibold text-slate-800">Endpoint readiness</h3>
        <el-tag :type="data?.status.ready ? 'success' : 'warning'">{{ data?.status.ready ? 'ready' : 'needs config' }}</el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="(ready, name) in data?.endpoint_readiness || {}" :key="name" class="rounded border border-slate-200 p-3">
          <p class="text-sm capitalize text-slate-600">{{ name }}</p>
          <el-tag class="mt-2" size="small" :type="ready ? 'success' : 'danger'">{{ ready ? 'ready' : 'not ready' }}</el-tag>
        </div>
      </div>
      <div v-if="data?.status.missing_config.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="item in data.status.missing_config" :key="item" type="warning" effect="plain">{{ item }}</el-tag>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[0.9fr_1.4fr]">
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Staging connection</h3>
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
              {{ data?.portal_contract.server_to_server_auth.required ? 'token required' : 'token optional' }}
            </el-tag>
            <el-tag :type="data?.portal_contract.server_to_server_auth.token_configured ? 'success' : 'warning'" effect="plain">
              {{ data?.portal_contract.server_to_server_auth.token_configured ? 'token configured' : 'token missing' }}
            </el-tag>
            <el-tag :type="data?.portal_contract.safety.token_value_exposed ? 'danger' : 'success'" effect="plain">
              {{ data?.portal_contract.safety.token_value_exposed ? 'token exposed' : 'token hidden' }}
            </el-tag>
          </div>
          <div>
            <dt class="text-slate-500">Allowed origins</dt>
            <dd class="mt-1 flex flex-wrap gap-2">
              <el-tag v-for="origin in data?.portal_contract.allowed_origins || []" :key="origin" effect="plain">{{ origin }}</el-tag>
              <span v-if="!data?.portal_contract.allowed_origins.length" class="text-slate-500">-</span>
            </dd>
          </div>
        </dl>
      </div>

      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Portal contract</h3>
        <el-table :data="data?.portal_contract.endpoints || []" class="w-full">
          <el-table-column prop="method" label="Method" width="90" />
          <el-table-column prop="name" label="Data" width="140" />
          <el-table-column prop="path" label="Path" min-width="310" />
          <el-table-column label="Ready" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.ready ? 'success' : 'warning'">{{ row.ready ? 'ready' : 'check' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Customer field contract</h3>
        <el-tag :type="data?.portal_contract.field_contract.date_policy.planned_dates_are_guarantees ? 'danger' : 'success'" effect="plain">
          {{ data?.portal_contract.field_contract.date_policy.planned_dates_are_guarantees ? 'date guarantee risk' : 'planned dates only' }}
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
        <h3 class="mb-3 font-semibold text-slate-800">Recent customer-visible orders</h3>
        <el-table :data="data?.recent_customer_visible_orders.items || []" v-loading="loading" class="w-full">
          <el-table-column prop="order_number" label="Order" width="160" />
          <el-table-column prop="company_name" label="Company" min-width="180" />
          <el-table-column prop="status" label="Status" width="170" />
          <el-table-column label="Total" width="150">
            <template #default="{ row }">{{ row.grand_total || '-' }} {{ row.currency }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Shipment status</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in data?.shipment_status_counts || {}" :key="status" effect="plain">
            {{ status }} {{ count }}
          </el-tag>
          <span v-if="!Object.keys(data?.shipment_status_counts || {}).length" class="text-sm text-slate-500">No shipment plans</span>
        </div>
        <h3 class="mb-3 mt-5 font-semibold text-slate-800">Feedback status</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in data?.feedback_status_counts || {}" :key="status" effect="plain">
            {{ status }} {{ count }}
          </el-tag>
          <span v-if="!Object.keys(data?.feedback_status_counts || {}).length" class="text-sm text-slate-500">No tickets</span>
        </div>
        <div class="mt-4 grid gap-2 sm:grid-cols-2">
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">Needs review</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.needs_internal_review_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">High priority</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.high_priority_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">Ready to close</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.ready_to_close_count ?? 0 }}</p>
          </div>
          <div class="rounded border border-slate-200 p-3">
            <p class="text-sm text-slate-500">Oldest open</p>
            <p class="mt-1 font-medium text-slate-800">{{ data?.feedback_operations.oldest_open_age_days ?? '-' }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Multi-partner flow readiness</h3>
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
          <p class="text-sm text-slate-500">With shipments</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partners_with_shipments ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">With risk</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.partners_with_risk ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Ranked</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.multi_partner_flow_readiness.safety.partner_ranked ? 'yes' : 'no' }}</p>
        </div>
      </div>
      <el-table :data="data?.multi_partner_flow_readiness.items || []" class="w-full">
        <el-table-column prop="partner_name" label="Partner" min-width="180" />
        <el-table-column prop="partner_type" label="Type" width="140" />
        <el-table-column prop="order_count" label="Orders" width="100" />
        <el-table-column prop="split_count" label="Splits" width="100" />
        <el-table-column prop="line_item_count" label="Lines" width="100" />
        <el-table-column prop="active_shipment_count" label="Shipments" width="120" />
        <el-table-column label="Risk" min-width="220">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-for="flag in row.risk_flags" :key="flag" size="small" type="warning" effect="plain">{{ flag }}</el-tag>
              <span v-if="!row.risk_flags.length" class="text-sm text-slate-500">clear</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Customer snapshots</h3>
        <el-tag :type="data?.customer_snapshot_readiness.portal_ready ? 'success' : 'warning'" effect="plain">
          {{ data?.customer_snapshot_readiness.portal_ready ? 'portal ready' : 'needs data' }}
        </el-tag>
      </div>
      <div class="mb-4 grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Snapshots</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.snapshot_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Production visible</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.production_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Active shipments</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.active_shipment_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Open feedback</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.customer_snapshot_readiness.open_feedback_count ?? 0 }}</p>
        </div>
      </div>
      <div class="mb-4 flex flex-wrap gap-2">
        <el-tag v-for="(count, stage) in data?.customer_snapshot_readiness.stage_counts || {}" :key="stage" effect="plain">
          {{ stage }} {{ count }}
        </el-tag>
        <el-tag v-if="data?.customer_snapshot_readiness.missing_progress_count" type="warning" effect="plain">
          missing progress {{ data.customer_snapshot_readiness.missing_progress_count }}
        </el-tag>
      </div>
      <el-table :data="data?.customer_snapshots || []" class="w-full">
        <el-table-column label="Order" width="170">
          <template #default="{ row }">{{ row.order.order_number }}</template>
        </el-table-column>
        <el-table-column label="Customer stage" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.customer_status.label }}</div>
            <div class="text-xs text-slate-500">{{ row.customer_status.stage }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Next action" min-width="240">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.customer_status.next_action_label }}</div>
            <div class="text-xs text-slate-500">{{ row.customer_status.next_action_detail }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Progress" min-width="260">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag
                v-for="step in row.customer_status.progress_steps"
                :key="step.key"
                size="small"
                :type="step.state === 'current' ? 'warning' : step.state === 'complete' ? 'success' : 'info'"
                effect="plain"
              >
                {{ step.label }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Shipment" width="160">
          <template #default="{ row }">active {{ row.shipment.active_count }}</template>
        </el-table-column>
        <el-table-column label="Signals" min-width="210">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-if="row.tracking_summary.has_production_updates" size="small" effect="plain">production</el-tag>
              <el-tag v-if="row.tracking_summary.has_active_shipment" size="small" effect="plain">shipment</el-tag>
              <el-tag v-if="row.tracking_summary.has_visible_resources" size="small" effect="plain">resources</el-tag>
              <el-tag v-if="row.tracking_summary.has_open_feedback" size="small" type="warning" effect="plain">feedback</el-tag>
              <span
                v-if="
                  !row.tracking_summary.has_production_updates &&
                  !row.tracking_summary.has_active_shipment &&
                  !row.tracking_summary.has_visible_resources &&
                  !row.tracking_summary.has_open_feedback
                "
                class="text-sm text-slate-500"
              >
                none
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Open feedback" width="150">
          <template #default="{ row }">{{ row.feedback.open_count }}</template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Resource readiness</h3>
        <el-tag :type="data?.resource_readiness.ready ? 'success' : 'warning'" effect="plain">
          {{ data?.resource_readiness.ready ? 'visible resources' : 'no visible resources' }}
        </el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-4">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Portal visible</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.portal_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Customer visible</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.customer_visible_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Needs publish</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.blocked_visibility_count ?? 0 }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Hidden published</p>
          <p class="mt-1 font-medium text-slate-800">{{ data?.resource_readiness.hidden_published_count ?? 0 }}</p>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="(count, status) in data?.resource_readiness.status_counts || {}" :key="status" effect="plain">
          {{ status }} {{ count }}
        </el-tag>
        <el-tag :type="data?.resource_readiness.safety.download_links_signed ? 'success' : 'danger'" effect="plain">
          {{ data?.resource_readiness.safety.download_links_signed ? 'signed downloads' : 'unsigned downloads' }}
        </el-tag>
        <el-tag :type="data?.resource_readiness.safety.file_location_exposed ? 'danger' : 'success'" effect="plain">
          {{ data?.resource_readiness.safety.file_location_exposed ? 'file path exposed' : 'paths hidden' }}
        </el-tag>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Market response signals</h3>
        <el-tag type="info" effect="plain">advisory only</el-tag>
      </div>
      <el-table :data="data?.market_signal_preview.items || []" class="w-full">
        <el-table-column prop="label" label="Focus" min-width="190" />
        <el-table-column prop="order_line_count" label="Order lines" width="120" />
        <el-table-column prop="ordered_quantity" label="Qty" width="100" />
        <el-table-column prop="feedback_count" label="Feedback" width="110" />
        <el-table-column prop="delayed_or_blocked_production_count" label="Production risk" width="150" />
        <el-table-column prop="shipment_issue_count" label="Shipment risk" width="140" />
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">Recent feedback tickets</h3>
      <el-table :data="data?.recent_feedback_tickets || []" class="w-full">
        <el-table-column prop="ticket_number" label="Ticket" width="150" />
        <el-table-column prop="subject" label="Subject" min-width="220" />
        <el-table-column prop="feedback_type" label="Type" width="130" />
        <el-table-column prop="status" label="Status" width="130" />
        <el-table-column prop="priority" label="Priority" width="120" />
        <el-table-column prop="internal_owner" label="Owner" width="150" />
        <el-table-column label="Review" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="row.operation.needs_internal_review ? 'warning' : 'success'" effect="plain">
              {{ row.operation.needs_internal_review ? 'review' : 'clear' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Age" width="90">
          <template #default="{ row }">{{ row.operation.age_days ?? '-' }}</template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { formatApiError } from '@/api/errors'
import { fetchPortalOperationsConsole, type PortalOperationsConsole } from '@/api/portalOperations'

const data = ref<PortalOperationsConsole | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPortalOperationsConsole()
  } catch (e) {
    error.value = formatApiError(e, 'Failed to load Portal operations console.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
