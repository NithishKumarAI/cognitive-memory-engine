import api from "@/services/api";
import type {
  LearningAction,
  LearningActionCreate,
  LearningActionUpdate,
  LearningOverview,
  ResumableCheckpoint,
  EvidenceRecommendation,
  TopicContinuity,
} from "@/types/continuity";

export async function getLearningOverview(timezone?: string) {
  const params = timezone ? { timezone } : {};
  const response = await api.get<LearningOverview>("/learning/overview", { params });
  return response.data;
}

export async function getCheckpoints(trackId?: number, limit?: number) {
  const params: Record<string, string | number> = {};
  if (trackId !== undefined) params.track_id = trackId;
  if (limit !== undefined) params.limit = limit;
  const response = await api.get<ResumableCheckpoint[]>("/learning/checkpoints", { params });
  return response.data;
}

export async function getLearningRecommendations(limit?: number) {
  const params = limit !== undefined ? { limit } : {};
  const response = await api.get<EvidenceRecommendation[]>("/learning/recommendations", { params });
  return response.data;
}

export async function getTopicContinuity(trackId?: number, limit?: number) {
  const params: Record<string, string | number> = {};
  if (trackId !== undefined) params.track_id = trackId;
  if (limit !== undefined) params.limit = limit;
  const response = await api.get<TopicContinuity[]>("/learning/topics", { params });
  return response.data;
}

export async function recordLearningAction(payload: LearningActionCreate) {
  const response = await api.post<LearningAction>("/learning/actions", payload);
  return response.data;
}

export async function updateLearningAction(actionId: number, payload: LearningActionUpdate) {
  const response = await api.patch<LearningAction>(`/learning/actions/${actionId}`, payload);
  return response.data;
}
