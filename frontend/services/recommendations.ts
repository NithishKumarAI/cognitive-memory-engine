import api from "@/services/api";
import type { DailyRecommendations } from "@/types/recommendation";

export async function getDailyRecommendations() {
  const response = await api.get<DailyRecommendations>("/recommendations/daily");
  return response.data;
}
