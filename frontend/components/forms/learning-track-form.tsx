"use client";

import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { LearningTrack, LearningTrackPayload } from "@/types/learningTrack";

type LearningTrackFormProps = {
  initialValue?: LearningTrack | null;
  onCancel: () => void;
  onSubmit: (payload: LearningTrackPayload) => Promise<void>;
};

export function LearningTrackForm({ initialValue, onCancel, onSubmit }: LearningTrackFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
  } = useForm<LearningTrackPayload>({
    defaultValues: {
      description: initialValue?.description ?? "",
      name: initialValue?.name ?? "",
    },
  });

  return (
    <form
      className="grid gap-5"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          description: values.description?.trim() || null,
          name: values.name.trim(),
        });
      })}
    >
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          {...register("name", {
            minLength: { message: "Name must be at least 2 characters.", value: 2 },
            required: "Name is required.",
          })}
        />
        {errors.name ? <p className="text-sm text-destructive">{errors.name.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea id="description" {...register("description")} />
      </div>

      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} type="button" variant="outline">
          Cancel
        </Button>
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
          {initialValue ? "Save changes" : "Create track"}
        </Button>
      </div>
    </form>
  );
}
