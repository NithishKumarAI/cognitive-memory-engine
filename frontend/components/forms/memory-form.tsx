"use client";

import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Memory, MemoryPayload } from "@/types/memory";
import type { StudyLog } from "@/types/studyLog";

type MemoryFormValues = Omit<MemoryPayload, "study_log_id"> & {
  study_log_id: string;
};

type MemoryFormProps = {
  initialValue?: Memory | null;
  onCancel: () => void;
  onSubmit: (payload: MemoryPayload) => Promise<void>;
  studyLogs: StudyLog[];
};

export function MemoryForm({ initialValue, onCancel, onSubmit, studyLogs }: MemoryFormProps) {
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
  } = useForm<MemoryFormValues>({
    defaultValues: {
      category: initialValue?.category ?? "",
      content: initialValue?.content ?? "",
      study_log_id: initialValue?.study_log_id ? String(initialValue.study_log_id) : "",
      title: initialValue?.title ?? "",
    },
  });

  return (
    <form
      className="grid gap-5"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          category: values.category.trim(),
          content: values.content.trim(),
          study_log_id: values.study_log_id ? Number(values.study_log_id) : null,
          title: values.title.trim(),
        });
      })}
    >
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register("title", { required: "Title is required." })} />
          {errors.title ? <p className="text-sm text-destructive">{errors.title.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Input id="category" {...register("category", { required: "Category is required." })} />
          {errors.category ? (
            <p className="text-sm text-destructive">{errors.category.message}</p>
          ) : null}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="study_log_id">Study Log</Label>
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="study_log_id"
          {...register("study_log_id")}
        >
          <option value="">No study log</option>
          {studyLogs.map((log) => (
            <option key={log.id} value={log.id}>
              {log.topic}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="content">Content</Label>
        <Textarea
          className="min-h-36"
          id="content"
          {...register("content", { required: "Content is required." })}
        />
        {errors.content ? <p className="text-sm text-destructive">{errors.content.message}</p> : null}
      </div>

      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} type="button" variant="outline">
          Cancel
        </Button>
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
          {initialValue ? "Save changes" : "Create memory"}
        </Button>
      </div>
    </form>
  );
}
