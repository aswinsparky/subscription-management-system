export interface Variant {
  id: number;
  product_id: number;
  variant_name: string;
  sku?: string | null;
  additional_price: string;
  is_active: boolean;
  created_at: string;
  final_price: string;
}

export interface Product {
  id: number;
  product_code: string;
  name: string;
  product_type: 'SERVICE' | 'SOFTWARE' | 'HARDWARE' | 'CONSUMABLE';
  description?: string | null;
  sales_price: string;
  cost_price: string;
  internal_notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  variants: Variant[];
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
