export interface Customer {
  id: number;
  customer_code: string;
  user_id?: number | null;
  full_name: string;
  email: string;
  phone?: string | null;
  company_name?: string | null;
  billing_address: string;
  tax_id?: string | null;
  account_status: 'ACTIVE' | 'SUSPENDED' | 'ARCHIVED';
  created_at: string;
  updated_at: string;
}

export interface CustomerListResponse {
  items: Customer[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SubscriptionSummary {
  id: number;
  subscription_number: string;
  status: string;
  billing_interval: string;
  total_amount: string;
  start_date: string;
  expiry_date: string;
  next_billing_date: string;
}

export interface QuotationSummary {
  id: number;
  quotation_number: string;
  status: string;
  total: string;
  quotation_date: string;
  expiration_date: string;
}

export interface CustomerHistoryResponse {
  customer: Customer;
  subscriptions: SubscriptionSummary[];
  quotations: QuotationSummary[];
}
