// Mirrors backend app/constants/status_enums.py string values for dropdowns and pipelines.

export const LEAD_STAGES = [
  'New',
  'Researched',
  'Contacted',
  'Connected',
  'Replied',
  'Interested',
  'Meeting Scheduled',
  'Sample Requested',
  'RFQ Created',
  'Quotation Sent',
  'Negotiating',
  'Won',
  'Lost',
  'Dormant',
] as const

export const RFQ_STATUSES = [
  'Draft',
  'Waiting for Internal Review',
  'Waiting for Partner Quote',
  'Partner Quoted',
  'Internal Costing',
  'Quotation Prepared',
  'Sent to Customer',
  'Customer Reviewing',
  'Negotiating',
  'Accepted',
  'Rejected',
  'Closed',
] as const

export const RFQ_CANDIDATE_STATUSES = [
  'Candidate',
  'Quote Requested',
  'Quote Received',
  'Under Review',
  'Preferred',
  'Not Suitable',
  'Rejected',
] as const

export const SAMPLE_STATUSES = [
  'Requested',
  'Internal Review',
  'Waiting for Partner',
  'Ready',
  'Shipped',
  'Delivered',
  'Feedback Received',
  'Converted',
  'Closed',
] as const

export const ORDER_PRODUCTION_STATUSES = [
  'Draft',
  'Order Confirmed',
  'Material Preparation',
  'Production',
  'Assembly',
  'Testing',
  'Packaging',
  'Ready to Ship',
  'Shipped',
  'Delivered',
  'Closed',
] as const

export const ORDER_SHIPPING_STATUSES = [
  'Not Started',
  'Booking',
  'Trucking to Port',
  'Customs Declaration',
  'Vessel Departed',
  'Vessel Arrived',
  'U.S. Customs',
  'Warehouse Inbound',
  'Final Delivery',
  'Delivered',
] as const

export const TASK_STATUSES = ['open', 'in_progress', 'done', 'cancelled'] as const

export const PRIORITY_LEVELS = ['low', 'medium', 'high', 'urgent'] as const

export const RISK_LEVELS = ['low', 'medium', 'high', 'critical'] as const

/** Backend milestone row statuses (MilestoneUpdate); lowercase in API after validation. */
export const MILESTONE_ROW_STATUSES = [
  'pending',
  'in_progress',
  'completed',
  'delayed',
  'done',
  'complete',
] as const
