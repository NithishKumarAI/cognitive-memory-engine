export type Memory = {
  id: number;
  user_id: number;
  study_log_id: number | null;
  title: string;
  content: string;
  category: string;
};

export type MemoryPayload = {
  title: string;
  content: string;
  category: string;
  study_log_id?: number | null;
};
