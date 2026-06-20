export type StudyLog = {
  id: number;
  user_id: number;
  topic: string;
  duration_minutes: number;
  notes: string;
  learning_track_id: number | null;
  created_at: string;
};

export type StudyLogPayload = {
  topic: string;
  duration_minutes: number;
  notes: string;
  learning_track_id?: number | null;
};
