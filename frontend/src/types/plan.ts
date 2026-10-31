export interface Plan {
  id: number;
  plan_code: string;
  name: string;
  description?: string | null;
  billing_interval: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY';
  plan_price: string;
  minimum_quantity: number;
  available_from?: string | null;
  available_until?: string | null;
  auto_close_enabled: boolean;
  early_cancellation_allowed: boolean;
  pause_allowed: boolean;
  renewal_allowed: boolean;
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  created_at: string;
  updated_at: string;
}

export interface PlanListResponse {
  items: Plan[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

