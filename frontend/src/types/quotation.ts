export interface QuotationItem {
  id: number;
  product_id: number;
  product_name?: string | null;
  variant_id?: number | null;
  variant_name?: string | null;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface Quotation {
  id: number;
  quotation_number: string;
  customer_id: number;
  customer_name?: string | null;
  customer_code?: string | null;
  plan_id: number;
  plan_name?: string | null;
  template_id?: number | null;
  quotation_date: string;
  expiration_date: string;
  subtotal: string;
  tax_reference?: string | null;
  tax_amount: string;
  total: string;
  status: 'DRAFT' | 'SENT' | 'ACCEPTED' | 'EXPIRED' | 'REJECTED';
  converted_to_subscription_id?: number | null;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
  items: QuotationItem[];
}

export interface QuotationListResponse {
  items: Quotation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ConvertQuotationResponse {
  message: string;
  quotation_id: number;
  subscription_id: number;
  subscription_number: string;
}
