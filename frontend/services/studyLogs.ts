import api from "@/services/api";
import type { StudyLog, StudyLogPayload } from "@/types/studyLog";

export async function listStudyLogs() {
  const response = await api.get<StudyLog[]>("/study-logs/");
  return response.data;
}

export async function createStudyLog(payload: StudyLogPayload) {
  const response = await api.post<StudyLog>("/study-logs/", payload);
  return response.data;
}

export async function updateStudyLog(id: number, payload: StudyLogPayload) {
  const response = await api.put<StudyLog>(`/study-logs/${id}`, payload);
  return response.data;
}

export async function deleteStudyLog(id: number) {
  await api.delete(`/study-logs/${id}`);
}
