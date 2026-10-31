export interface DueSubscription {
  subscription_id: number;
  subscription_number: string;
  customer_id: number;
  customer_name: string;
  plan_name: string;
  billing_interval: string;
  amount: number | string;
  current_period_end: string;
  next_billing_date: string;
  days_until_due: number;
  idempotency_key: string;
}

export interface RenewalBillingRequest {
  id: number;
  idempotency_key: string;
  subscription_id: number;
  subscription_number?: string | null;
  customer_id: number;
  customer_name?: string | null;
  billing_period_start: string;
  billing_period_end: string;
  amount: number | string;
  status: 'PENDING' | 'PROCESSED' | 'FAILED';
  invoice_reference?: string | null;
  retry_count: number;
  last_error?: string | null;
  created_at: string;
}

export interface BatchRenewalResult {
  total_due: number;
  processed_count: number;
  failed_count: number;
  details: RenewalBillingRequest[];
}

