import api from "@/services/api";
import type { LearningTrack, LearningTrackPayload } from "@/types/learningTrack";

export async function listLearningTracks() {
  const response = await api.get<LearningTrack[]>("/learning-tracks");
  return response.data;
}

export async function createLearningTrack(payload: LearningTrackPayload) {
  const response = await api.post<LearningTrack>("/learning-tracks", payload);
  return response.data;
}

export async function updateLearningTrack(id: number, payload: LearningTrackPayload) {
  const response = await api.put<LearningTrack>(`/learning-tracks/${id}`, payload);
  return response.data;
}

export async function deleteLearningTrack(id: number) {
  await api.delete(`/learning-tracks/${id}`);
}
