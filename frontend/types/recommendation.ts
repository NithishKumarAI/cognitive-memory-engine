export type RecommendationPriority = "high" | "medium" | "low";

export type Recommendation = {
  type: string;
  priority: RecommendationPriority;
  message: string;
};

export type DailyRecommendations = {
  generated_at: string;
  recommendations: Recommendation[];
};
