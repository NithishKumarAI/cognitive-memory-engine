export type LearningTrack = {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  created_at: string;
};

export type LearningTrackPayload = {
  name: string;
  description?: string | null;
};
