export type RAGSource = {
  source_type?: string;
  memory_id?: number | null;
  observation_id?: number | null;
  capture_id?: number | null;
  title: string;
  category: string;
  distance: number;
  evidence?: string | null;
};

export type RAGRequest = {
  question: string;
  top_k?: number;
};

export type RAGResponse = {
  answer: string;
  sources: RAGSource[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: RAGSource[];
};
