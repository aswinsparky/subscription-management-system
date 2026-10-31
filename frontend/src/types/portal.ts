import { Subscription } from './subscription';
import { Quotation } from './quotation';

export interface CustomerProfile {
  id: number;
  customer_code: string;
  user_id?: number | null;
  full_name: string;
  email: string;
  phone?: string | null;
  company_name?: string | null;
  billing_address: string;
  tax_id?: string | null;
  account_status: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerPortalOverview {
  profile: CustomerProfile;
  active_subscriptions: Subscription[];
  pending_quotations: Quotation[];
  total_active_mrr: number | string;
}
