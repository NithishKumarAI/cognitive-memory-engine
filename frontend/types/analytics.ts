export type AnalyticsOverview = {
  total_study_logs: number;
  total_topics: number;
  total_hours: number;
  current_streak: number;
  consistency_score: number;
};

export type TopicDistributionItem = {
  topic: string;
  total_minutes: number;
  total_hours: number;
  session_count: number;
};

export type DailyActivityItem = {
  date: string;
  study_minutes: number;
};

export type Consistency = {
  current_streak: number;
  frequency_percentage: number;
  consistency_score: number;
};
