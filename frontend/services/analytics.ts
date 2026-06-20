import api from "@/services/api";
import type {
  AnalyticsOverview,
  Consistency,
  DailyActivityItem,
  TopicDistributionItem,
} from "@/types/analytics";

export async function getAnalyticsOverview() {
  const response = await api.get<AnalyticsOverview>("/analytics/overview");
  return response.data;
}

export async function getTopicDistribution() {
  const response = await api.get<TopicDistributionItem[]>("/analytics/topic-distribution");
  return response.data;
}

export async function getDailyActivity() {
  const response = await api.get<DailyActivityItem[]>("/analytics/daily-activity");
  return response.data;
}

export async function getConsistency() {
  const response = await api.get<Consistency>("/analytics/consistency");
  return response.data;
}
