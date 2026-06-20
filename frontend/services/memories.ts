import api from "@/services/api";
import type { Memory, MemoryPayload } from "@/types/memory";

export async function listMemories() {
  const response = await api.get<Memory[]>("/memories");
  return response.data;
}

export async function getMemory(id: number) {
  const response = await api.get<Memory>(`/memories/${id}`);
  return response.data;
}

export async function createMemory(payload: MemoryPayload) {
  const response = await api.post<Memory>("/memories", payload);
  return response.data;
}

export async function updateMemory(id: number, payload: MemoryPayload) {
  const response = await api.put<Memory>(`/memories/${id}`, payload);
  return response.data;
}

export async function deleteMemory(id: number) {
  await api.delete(`/memories/${id}`);
}
