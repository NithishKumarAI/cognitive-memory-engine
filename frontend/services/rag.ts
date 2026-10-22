import api from "@/services/api";
import type { RAGRequest, RAGResponse } from "@/types/rag";

export async function askRag(payload: RAGRequest) {
  const response = await api.post<RAGResponse>("/rag/ask", payload);
  return response.data;
}

export type PreviousConversation = { id: number; message: string; response: string; created_at: string | null };
export async function getChatHistory(beforeId?: number) {
  return (await api.get<PreviousConversation[]>("/rag/history", { params: { before_id: beforeId, limit: 20 } })).data;
}
