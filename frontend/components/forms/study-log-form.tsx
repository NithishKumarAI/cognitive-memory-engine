"use client";

import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { LearningTrack } from "@/types/learningTrack";
import type { StudyLog, StudyLogPayload } from "@/types/studyLog";

type StudyLogFormValues = Omit<StudyLogPayload, "duration_minutes" | "learning_track_id"> & {
  duration_minutes: string;
  learning_track_id: string;
};

type StudyLogFormProps = {
  initialValue?: StudyLog | null;
  learningTracks: LearningTrack[];
  onCancel: () => void;
  onSubmit: (payload: StudyLogPayload) => Promise<void>;
};

export function StudyLogForm({ initialValue, learningTracks, onCancel, onSubmit }: StudyLogFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
  } = useForm<StudyLogFormValues>({
    defaultValues: {
      duration_minutes: initialValue?.duration_minutes ? String(initialValue.duration_minutes) : "30",
      learning_track_id: initialValue?.learning_track_id ? String(initialValue.learning_track_id) : "",
      notes: initialValue?.notes ?? "",
      topic: initialValue?.topic ?? "",
    },
  });

  return (
    <form
      className="grid gap-5"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          duration_minutes: Number(values.duration_minutes),
          learning_track_id: values.learning_track_id ? Number(values.learning_track_id) : null,
          notes: values.notes.trim(),
          topic: values.topic.trim(),
        });
      })}
    >
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="topic">Topic</Label>
          <Input id="topic" {...register("topic", { required: "Topic is required." })} />
          {errors.topic ? <p className="text-sm text-destructive">{errors.topic.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="duration_minutes">Duration</Label>
          <Input
            id="duration_minutes"
            min={1}
            type="number"
            {...register("duration_minutes", {
              min: { message: "Duration must be at least 1 minute.", value: 1 },
              required: "Duration is required.",
            })}
          />
          {errors.duration_minutes ? (
            <p className="text-sm text-destructive">{errors.duration_minutes.message}</p>
          ) : null}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="learning_track_id">Learning Track</Label>
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="learning_track_id"
          {...register("learning_track_id")}
        >
          <option value="">No track</option>
          {learningTracks.map((track) => (
            <option key={track.id} value={track.id}>
              {track.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea id="notes" {...register("notes", { required: "Notes are required." })} />
        {errors.notes ? <p className="text-sm text-destructive">{errors.notes.message}</p> : null}
      </div>

      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} type="button" variant="outline">
          Cancel
        </Button>
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
          {initialValue ? "Save changes" : "Create log"}
        </Button>
      </div>
    </form>
  );
}
