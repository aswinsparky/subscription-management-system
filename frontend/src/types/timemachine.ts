export interface StateSnapshot {
  status: string;
  total_amount: string;
  billing_interval: string;
  current_period_start?: string | null;
  current_period_end?: string | null;
  next_billing_date?: string | null;
  auto_renew: boolean;
}

export interface TimelineEvent {
  id: number;
  subscription_id: number;
  event_type: string;
  timestamp: string;
  actor_email?: string | null;
  actor_role?: string | null;
  reason?: string | null;
  previous_state?: Record<string, any> | null;
  new_state: Record<string, any>;
  metadata_json?: Record<string, any> | null;
  diff_fields: Record<string, { from: any; to: any }>;
}

export interface TimeMachineReconstruction {
  subscription_id: number;
  subscription_number: string;
  customer_name: string;
  target_timestamp: string;
  events_replayed_count: number;
  total_events_count: number;
  reconstructed_state: StateSnapshot;
  current_live_state: StateSnapshot;
  last_applied_event?: TimelineEvent | null;
}

export interface SimulationResult {
  subscription_id: number;
  action: string;
  is_allowed: boolean;
  rejection_reason?: string | null;
  current_state: StateSnapshot;
  predicted_state?: StateSnapshot | null;
  policy_checks: Record<string, boolean>;
}
