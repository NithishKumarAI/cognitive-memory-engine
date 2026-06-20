import api from "@/services/api";
import type { RAGRequest, RAGResponse } from "@/types/rag";

export async function askRag(payload: RAGRequest) {
  const response = await api.post<RAGResponse>("/rag/ask", payload);
  return response.data;
}
