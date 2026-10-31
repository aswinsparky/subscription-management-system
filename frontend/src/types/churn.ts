export interface ChurnRiskSignal {
  signal_key: string;
  signal_name: string;
  weight: number;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  description: string;
  recommended_action: string;
}

export interface CustomerRiskProfile {
  customer_id: number;
  customer_code: string;
  full_name: string;
  email: string;
  company_name?: string | null;
  risk_score: number;
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH';
  active_subscriptions_count: number;
  total_mrr: number | string;
  signals: ChurnRiskSignal[];
  suggested_retention_playbook: string;
}

export interface ChurnDashboardMetrics {
  total_customers_analyzed: number;
  avg_risk_score: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  at_risk_mrr: number | string;
  top_at_risk_customers: CustomerRiskProfile[];
}

export interface RetentionActionRequest {
  action_type: string;
  notes: string;
  discount_percent_offered?: number;
}

