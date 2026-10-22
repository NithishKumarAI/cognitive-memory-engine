export type LearningState =
  | "recorded"
  | "exploring"
  | "self_reported_understood"
  | "needs_attention"
  | "review_suggested"
  | "insufficient_evidence";

export type ActionType = "next_step" | "difficulty" | "question" | "review" | "recommendation";
export type ActionStatus = "completed" | "resolved" | "dismissed";

export type LearningActionCreate = {
  idempotency_key: string;
  action_type: ActionType;
  status: ActionStatus;
  observation_id?: number | null;
  capture_id?: number | null;
  learning_track_id?: number | null;
  topic?: string | null;
  recommendation_id?: string | null;
  notes?: string | null;
};

export type LearningActionUpdate = {
  status: ActionStatus;
  notes?: string | null;
};

export type LearningAction = {
  id: number;
  user_id: number;
  idempotency_key: string;
  action_type: string;
  status: string;
  observation_id?: number | null;
  capture_id?: number | null;
  learning_track_id?: number | null;
  topic?: string | null;
  recommendation_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type ObservationBrief = {
  id: number;
  observation_type: string;
  topic: string;
  content: string;
  evidence: string;
  capture_id: number;
  is_resolved: boolean;
  is_completed: boolean;
  is_dismissed: boolean;
  created_at: string;
};

export type ResumableCheckpoint = {
  topic: string;
  normalized_topic: string;
  learning_track_id?: number | null;
  learning_track_name?: string | null;
  state: LearningState;
  last_capture_id?: number | null;
  last_capture_at?: string | null;
  last_capture_excerpt?: string | null;
  latest_observation_id?: number | null;
  latest_observation_content?: string | null;
  understood_self_reports: ObservationBrief[];
  unresolved_difficulties: ObservationBrief[];
  unresolved_questions: ObservationBrief[];
  pending_next_steps: ObservationBrief[];
  review_suggested: boolean;
  days_since_last_activity: number;
};

export type EvidenceRecommendation = {
  id: string;
  type: string;
  priority: "high" | "medium" | "low";
  topic: string;
  learning_track_id?: number | null;
  learning_track_name?: string | null;
  action: string;
  reason: string;
  source_capture_id?: number | null;
  source_observation_id?: number | null;
  evidence?: string | null;
  review_due_at?: string | null;
  link_url?: string | null;
  status?: string | null;
};

export type TopicContinuity = {
  topic: string;
  normalized_topic: string;
  learning_track_id?: number | null;
  learning_track_name?: string | null;
  state: LearningState;
  confirmed_capture_count: number;
  observations_count: number;
  difficulties_count: number;
  unresolved_difficulties_count: number;
  questions_count: number;
  unresolved_questions_count: number;
  pending_next_steps_count: number;
  last_studied_at?: string | null;
  is_review_due: boolean;
};

export type LearningOverview = {
  confirmed_captures_count: number;
  distinct_topics_count: number;
  total_observations_count: number;
  learned_count: number;
  understood_count: number;
  difficulties_count: number;
  unresolved_difficulties_count: number;
  questions_count: number;
  unresolved_questions_count: number;
  pending_next_actions_count: number;
  total_logged_study_hours: number;
  latest_activity_at?: string | null;
  current_streak: number;
  review_suggested_count: number;
  checkpoints_count: number;
};
