export type RecommendationPriority = "high" | "medium" | "low";

export type Recommendation = {
  id?: string | null;
  type: string;
  priority: RecommendationPriority;
  message: string;
  topic?: string | null;
  learning_track_id?: number | null;
  learning_track_name?: string | null;
  action?: string | null;
  reason?: string | null;
  source_capture_id?: number | null;
  source_observation_id?: number | null;
  evidence?: string | null;
  review_due_at?: string | null;
  link_url?: string | null;
  status?: string | null;
};

export type DailyRecommendations = {
  generated_at: string;
  recommendations: Recommendation[];
};
