import { http } from '@/api/http'
import type { PortalFieldContract } from '@/api/portalCustomer'
import type { V1Envelope } from '@/api/quotes'

export interface PortalOperationsConsole {
  status: {
    ready: boolean
    enabled: boolean
    token_required: boolean
    token_configured: boolean
    public_base_url_configured: boolean
    public_base_url: string | null
    allowed_origins: string[]
    missing_config: string[]
  }
  portal_contract: {
    base_url: string | null
    server_to_server_auth: {
      required: boolean
      header_name: string
      bearer_authorization_supported: boolean
      token_configured: boolean
      token_value_exposed: boolean
    }
    allowed_origins: string[]
    missing_config: string[]
    field_contract: PortalFieldContract
    endpoints: Array<{
      name: string
      method: string
      path: string
      ready: boolean
    }>
    safety: {
      customer_visible_fields_only: boolean
      forbidden_field_filter_enabled: boolean
      token_value_exposed: boolean
      automatic_customer_notification: boolean
      carrier_api_called: boolean
    }
  }
  portal_launch_readiness: {
    ready_for_real_staging: boolean
    blockers: string[]
    warnings: string[]
    checks: {
      portal_api_enabled: boolean
      token_configured: boolean
      public_base_url_configured: boolean
      runtime_ok: boolean
      all_endpoints_ready: boolean
      forbidden_field_audit_clear: boolean
      customer_snapshots_ready: boolean
      resources_ready: boolean
      feedback_queue_clear: boolean
    }
    safety: {
      read_only: boolean
      staging_validated: boolean
      customer_notified: boolean
      supplier_notified: boolean
      automatic_reply_sent: boolean
      carrier_api_called: boolean
      token_value_exposed: boolean
    }
  }
  runtime_health: {
    ok: boolean
    database_status: string
    database_ready: boolean
    migration_pending: boolean
    alembic_current_revision: string | null
    alembic_head_revision: string | null
    portal_customer_api_ready: boolean
    warnings: string[]
    safety: {
      read_only: boolean
      secret_values_exposed: boolean
      database_url_exposed: boolean
      storage_path_exposed: boolean
    }
  }
  endpoint_readiness: Record<'products' | 'orders' | 'production' | 'shipment' | 'resources' | 'feedback', boolean>
  recent_customer_visible_orders: {
    items: Array<{
      id: string
      order_number: string
      status: string
      company_name: string | null
      grand_total: string | null
      currency: string
      portal_tracking: {
        snapshot_available: boolean
        stage: string | null
        label: string | null
        next_action_label: string | null
        active_shipment_count: number
        open_feedback_count: number
        has_production_updates: boolean
        has_active_shipment: boolean
        has_visible_resources: boolean
        has_open_feedback: boolean
        planned_dates_are_guarantees: boolean
      }
    }>
    total: number
  }
  customer_snapshots: Array<{
    order: { id: string; order_number: string; status: string }
    customer_status: {
      stage: string
      label: string
      next_action_label: string
      next_action_detail: string
      production_completed: boolean
      ready_to_ship: boolean
      shipped: boolean
      delivered: boolean
      current_step_index: number
      progress_steps: Array<{
        key: string
        label: string
        state: 'complete' | 'current' | 'pending'
        date: string | null
        planned_dates_are_guarantees: boolean
      }>
      planned_dates_are_guarantees: boolean
    }
    tracking_summary: {
      stage: string
      production_item_count: number
      shipment_item_count: number
      resource_visible_count: number
      feedback_open_count: number
      has_production_updates: boolean
      has_active_shipment: boolean
      has_visible_resources: boolean
      has_open_feedback: boolean
      planned_dates_are_guarantees: boolean
    }
    shipment: { status_counts: Record<string, number>; active_count: number }
    feedback: {
      submit_endpoint: string
      submit_method: string
      allowed_feedback_types: string[]
      allowed_priorities: string[]
      requires_order_id: boolean
      customer_name_required: boolean
      customer_email_required: boolean
      resolution_time_promised: boolean
      total_count: number
      open_count: number
      customer_notified: boolean
      automatic_reply_sent: boolean
    }
    safety: { forbidden_field_filter_enabled: boolean; token_exposed: boolean }
  }>
  customer_snapshot_readiness: {
    snapshot_count: number
    stage_counts: Record<string, number>
    missing_progress_count: number
    production_visible_count: number
    ready_to_ship_count: number
    shipped_count: number
    delivered_count: number
    active_shipment_count: number
    open_feedback_count: number
    action_items: Array<{
      order_id: string | null
      order_number: string | null
      stage: string
      label: string | null
      next_action_label: string | null
      active_shipment_count: number
      open_feedback_count: number
      action: string
      safety: {
        customer_visible_only: boolean
        read_only: boolean
        planned_dates_are_guarantees: boolean
        customer_notified: boolean
        supplier_notified: boolean
        order_status_mutated: boolean
        shipment_created: boolean
      }
    }>
    portal_ready: boolean
    safety: {
      customer_visible_only: boolean
      forbidden_field_filter_enabled: boolean
      planned_dates_are_guarantees: boolean
      customer_notified: boolean
      order_status_mutated: boolean
    }
  }
  resource_readiness: {
    total_count: number
    portal_visible_count: number
    customer_visible_count: number
    blocked_visibility_count: number
    hidden_published_count: number
    status_counts: Record<string, number>
    category_counts: Record<string, number>
    action_items: Array<{
      id: string
      order_id: string
      title: string
      category: string
      status: string
      customer_visible: boolean
      portal_visible: boolean
      action: string
      safety: {
        metadata_only: boolean
        download_url_exposed: boolean
        file_location_exposed: boolean
        filesystem_path_exposed: boolean
        token_value_exposed: boolean
        customer_notified: boolean
        automatic_email_sent: boolean
      }
    }>
    ready: boolean
    safety: {
      metadata_only: boolean
      download_links_signed: boolean
      file_location_exposed: boolean
      filesystem_path_exposed: boolean
      customer_notified: boolean
      automatic_email_sent: boolean
    }
  }
  multi_partner_flow_readiness: {
    partner_count: number
    order_count: number
    split_count: number
    partners_with_orders: number
    partners_with_production: number
    partners_with_shipments: number
    partners_with_risk: number
    items: Array<{
      partner_id: string
      partner_name: string
      partner_type: string | null
      order_count: number
      split_count: number
      line_item_count: number
      supplier_confirmation_status_counts: Record<string, number>
      milestone_status_counts: Record<string, number>
      shipment_status_counts: Record<string, number>
      active_shipment_count: number
      risk_flags: string[]
    }>
    safety: {
      read_only: boolean
      partner_neutral: boolean
      partner_ranked: boolean
      partner_selection_changed: boolean
      supplier_notified: boolean
      customer_notified: boolean
      order_status_mutated: boolean
      shipment_created: boolean
    }
  }
  shipment_status_counts: Record<string, number>
  feedback_status_counts: Record<string, number>
  feedback_priority_counts: Record<string, number>
  feedback_operations: {
    total_count: number
    open_count: number
    high_priority_count: number
    needs_internal_review_count: number
    response_summary_missing_count: number
    ready_to_close_count: number
    action_items: Array<{
      id: string
      ticket_number: string
      order_id: string | null
      feedback_type: string
      subject: string
      status: string
      priority: string
      internal_owner: string | null
      age_days: number | null
      action: string
      safety: {
        internal_queue_only: boolean
        customer_notified: boolean
        automatic_reply_sent: boolean
        email_sent: boolean
        sla_promised: boolean
      }
    }>
    oldest_open_age_days: number | null
    safety: {
      internal_queue_only: boolean
      customer_notified: boolean
      automatic_reply_sent: boolean
      sla_promised: boolean
    }
  }
  market_signal_preview: {
    items: Array<{
      key: string
      label: string
      order_line_count: number
      ordered_quantity: number
      feedback_count: number
      delayed_or_blocked_production_count: number
      shipment_issue_count: number
      human_review_required: boolean
    }>
    total: number
    safety: {
      read_only: boolean
      advisory_only: boolean
      human_review_required: boolean
      auto_ticket_created: boolean
      customer_notified: boolean
      supplier_notified: boolean
    }
  }
  recent_feedback_tickets: Array<{
    id: string
    ticket_number: string
    order_id: string | null
    feedback_type: string
    subject: string
    status: string
    priority: string
    internal_owner: string | null
    operation: {
      age_days: number | null
      open: boolean
      needs_internal_review: boolean
      response_summary_missing: boolean
      customer_visible_response: boolean
      internal_handling_only: boolean
    }
    created_at: string | null
  }>
  forbidden_field_audit: {
    checked: boolean
    checked_payloads: string[]
    hits: string[]
    credential_value_exposed: boolean
    server_file_path_exposed: boolean
    cost_fields_exposed: boolean
  }
  safety: {
    read_only: boolean
    customer_notified: boolean
    supplier_notified: boolean
    automatic_reply_sent: boolean
    carrier_api_called: boolean
    order_status_mutated: boolean
  }
}

export async function fetchPortalOperationsConsole(): Promise<PortalOperationsConsole> {
  const { data } = await http.get<V1Envelope<PortalOperationsConsole>>('/v1/portal/operations/console')
  return data.data
}
