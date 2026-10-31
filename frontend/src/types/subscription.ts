export type SubscriptionStatus =
  | 'DRAFT'
  | 'QUOTATION'
  | 'CONFIRMED'
  | 'ACTIVE'
  | 'PAUSED'
  | 'CANCELLED'
  | 'CLOSED';

export interface SubscriptionItem {
  id: number;
  subscription_id: number;
  product_id: number;
  variant_id?: number | null;
  product_name?: string | null;
  variant_name?: string | null;
  quantity: number;
  unit_price: number | string;
  subtotal: number | string;
}

export interface SubscriptionEvent {
  id: number;
  subscription_id: number;
  event_type: string;
  previous_state?: Record<string, any> | null;
  new_state: Record<string, any>;
  actor_id?: number | null;
  actor_email?: string | null;
  actor_role?: string | null;
  reason?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface CustomerSimple {
  id: number;
  customer_code: string;
  full_name: string;
  email: string;
  company_name?: string | null;
}

export interface PlanSimple {
  id: number;
  plan_code: string;
  name: string;
  billing_interval: string;
  plan_price: number | string;
  pause_allowed: boolean;
  early_cancellation_allowed: boolean;
  auto_close_enabled: boolean;
}

export interface Subscription {
  id: number;
  subscription_number: string;
  customer_id: number;
  plan_id: number;
  source_quotation_id?: number | null;
  start_date: string;
  expiry_date: string;
  billing_interval: string;
  payment_terms: string;
  subtotal: number | string;
  discount_reference?: string | null;
  discount_amount: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  status: SubscriptionStatus;
  next_billing_date: string;
  current_period_start: string;
  current_period_end: string;
  auto_renew: boolean;
  last_renewed_at?: string | null;
  cancellation_reason?: string | null;
  created_at: string;
  updated_at: string;

  customer?: CustomerSimple;
  plan?: PlanSimple;
  items: SubscriptionItem[];
  events: SubscriptionEvent[];
}

export interface SubscriptionListResponse {
  items: Subscription[];
  total: number;
  page: number;
  size: number;
}
