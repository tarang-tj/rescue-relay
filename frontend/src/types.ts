export type DecisionState = "pending" | "approved" | "rejected";
export type DispatchState = "proposed" | "awaiting_approval" | "scheduled" | "declined" | "message_sent";

export interface Allocation {
  pantry_id: string;
  pantry_name: string;
  pounds: number;
  reason: string;
}

export interface Dispatch {
  id: string;
  offer_id: string;
  donor: string;
  description: string;
  pounds: number;
  offered_pounds: number;
  unallocated_pounds: number;
  allocations: Allocation[];
  pickup_date: string | null;
  pickup_window: string;
  confidence: number;
  state: DispatchState;
  decision_ids: string[];
  evidence_ids: string[];
}

export interface Decision {
  id: string;
  kind: string;
  title: string;
  context: string;
  dispatch_id: string;
  state: DecisionState;
  created_at: string;
  resolved_at: string | null;
  resolution_note: string | null;
}

export interface MessageDraft {
  id: string;
  dispatch_id: string;
  recipient: string;
  subject: string;
  body: string;
  state: string;
  created_at: string;
}

export interface Evidence {
  id: string;
  kind: string;
  label: string;
  detail: string;
  captured_at: string;
}

export interface RunStep {
  id: string;
  tool: string;
  label: string;
  detail: string;
  status: string;
  started_at: string;
  duration_ms: number;
  evidence_ids: string[];
}

export interface AgentRun {
  id: string;
  mode: string;
  model_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  summary: string;
  steps: RunStep[];
  error: string | null;
}

export interface Dashboard {
  active_run: AgentRun | null;
  dispatches: Dispatch[];
  decisions: Decision[];
  message_drafts: MessageDraft[];
  evidence: Evidence[];
  impact: { pounds_matched: number; meals_estimated: number; minutes_saved: number };
  run_history: AgentRun[];
}
