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
    connection_guide: {
      consumer: string
      public_base_url: string | null
      auth: {
        header_name: string
        authorization_bearer_supported: boolean
        required: boolean
        configured: boolean
        value_exposed: boolean
      }
      allowed_origins: string[]
      required_environment: Array<{
        name: string
        required_value: string
        configured: boolean
        sensitive: boolean
        value_exposed: boolean
      }>
      smoke_sequence: Array<{
        key: string
        method: string
        path: string
        expected_status: number
        uses_order_id_from: string | null
        mutates_data: boolean
        test_only?: boolean
        subject_prefix?: string
      }>
      safety: {
        server_to_server_only: boolean
        browser_token_storage_allowed: boolean
        customer_visible_fields_only: boolean
        planned_dates_are_guarantees: boolean
        feedback_test_creates_ticket: boolean
        automatic_reply_sent: boolean
        customer_notified: boolean
        supplier_notified: boolean
        carrier_api_called: boolean
        deployment_triggered: boolean
        staging_validated: boolean
        token_value_exposed: boolean
      }
    }
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
      recent_order_snapshot_coverage: boolean
      shipments_ready: boolean
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
  staging_integration_checklist: {
    items: Array<{
      key: string
      label: string
      status: 'done' | 'blocked' | 'needs_operator_action' | 'ready_for_operator'
      action: string
      detail: string
      safety: {
        read_only: boolean
        staging_validated: boolean
        proof_record_created: boolean
        customer_notified: boolean
        supplier_notified: boolean
        automatic_reply_sent: boolean
        carrier_api_called: boolean
        token_value_exposed: boolean
      }
    }>
    total: number
    done_count: number
    blocked_count: number
    operator_action_count: number
    ready_for_staging_operator: boolean
    safety: {
      read_only: boolean
      staging_validated: boolean
      proof_record_created: boolean
      deployment_triggered: boolean
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
    portal_display: {
      headline: string
      stage: string
      stage_label: string
      current_step_label: string | null
      next_action_label: string
      next_action_detail: string
      progress_percent: number
      status_badges: Array<{
        key: string
        label: string
        state: 'complete' | 'current' | 'pending'
        active: boolean
        date: string | null
        planned_dates_are_guarantees: boolean
      }>
      signal_cards: Array<{ key: string; label: string; active: boolean; count: number }>
      feedback_cta: {
        label: string
        path: string
        customer_notified: boolean
        automatic_reply_sent: boolean
        resolution_time_promised: boolean
      }
      planned_dates_are_guarantees: boolean
    }
    customer_timeline?: {
      items: Array<{
        key: string
        source: string
        label: string
        status: string
        state: string
        occurred_at: string | null
        planned_at: string | null
        shipment_method?: string | null
        tracking_number_present?: boolean
        category?: string | null
        open_count?: number
        total_count?: number
        planned_dates_are_guarantees: boolean
      }>
      total: number
      has_attention: boolean
      planned_dates_are_guarantees: boolean
      safety: {
        customer_visible_only: boolean
        forbidden_field_filter_enabled: boolean
        planned_dates_are_guarantees: boolean
        customer_notified: boolean
        supplier_notified: boolean
        carrier_api_called: boolean
        order_status_mutated: boolean
      }
    }
    links: {
      order_detail: string
      order_snapshot: string
      production: string
      shipment: string
      resources: string
      feedback_submit: string
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
  snapshot_coverage: {
    recent_order_count: number
    snapshot_count: number
    missing_snapshot_count: number
    coverage_complete: boolean
    action_items: Array<{
      order_id: string | null
      order_number: string | null
      status: string | null
      action: string
      safety: {
        read_only: boolean
        customer_visible_only: boolean
        customer_notified: boolean
        supplier_notified: boolean
        order_status_mutated: boolean
        planned_dates_are_guarantees: boolean
      }
    }>
    safety: {
      read_only: boolean
      customer_visible_only: boolean
      forbidden_field_filter_enabled: boolean
      customer_notified: boolean
      supplier_notified: boolean
      order_status_mutated: boolean
      planned_dates_are_guarantees: boolean
    }
  }
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
  shipment_readiness: {
    total_count: number
    active_count: number
    planned_count: number
    shipped_count: number
    delivered_count: number
    cancelled_count: number
    missing_estimated_dates_count: number
    shipped_without_tracking_count: number
    status_counts: Record<string, number>
    action_items: Array<{
      id: string
      order_id: string
      partner_split_id: string | null
      status: string
      shipment_method: string | null
      estimated_ship_date: string | null
      estimated_arrival_date: string | null
      tracking_number_present: boolean
      action: string
      safety: {
        read_only: boolean
        carrier_api_called: boolean
        shipment_created: boolean
        customer_notified: boolean
        supplier_notified: boolean
        order_status_mutated: boolean
        tracking_number_value_exposed: boolean
        planned_dates_are_guarantees: boolean
      }
    }>
    ready: boolean
    safety: {
      read_only: boolean
      customer_visible_metadata_only: boolean
      carrier_api_called: boolean
      shipment_created: boolean
      customer_notified: boolean
      supplier_notified: boolean
      order_status_mutated: boolean
      tracking_number_values_exposed: boolean
      planned_dates_are_guarantees: boolean
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
      action_label: string
      route_query: {
        ticket_id: string
        operation_filter: string
        status: string
        priority: string | null
        feedback_type: string
      }
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
