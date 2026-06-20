export type RAGSource = {
  memory_id: number;
  title: string;
  category: string;
  distance: number;
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
