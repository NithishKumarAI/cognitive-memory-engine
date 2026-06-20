"use client";

import { AxiosError } from "axios";
import { Edit, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { EntityTable } from "@/components/dashboard/entity-table";
import { FormShell } from "@/components/dashboard/form-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { LearningTrackForm } from "@/components/forms/learning-track-form";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  createLearningTrack,
  deleteLearningTrack,
  listLearningTracks,
  updateLearningTrack,
} from "@/services/learningTracks";
import type { LearningTrack, LearningTrackPayload } from "@/types/learningTrack";

export default function LearningTracksPage() {
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTrack, setSelectedTrack] = useState<LearningTrack | null>(null);
  const [tracks, setTracks] = useState<LearningTrack[]>([]);

  async function loadTracks() {
    setIsLoading(true);
    setError(null);

    try {
      setTracks(await listLearningTracks());
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to load learning tracks."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // Page data is loaded from the API when this protected client route mounts.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadTracks();
  }, []);

  async function handleSubmit(payload: LearningTrackPayload) {
    if (formMode === "edit" && selectedTrack) {
      await updateLearningTrack(selectedTrack.id, payload);
    } else {
      await createLearningTrack(payload);
    }

    closeForm();
    await loadTracks();
  }

  async function handleDelete(track: LearningTrack) {
    const confirmed = window.confirm(`Delete "${track.name}"?`);

    if (!confirmed) {
      return;
    }

    try {
      await deleteLearningTrack(track.id);
      await loadTracks();
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to delete learning track."));
    }
  }

  function closeForm() {
    setFormMode(null);
    setSelectedTrack(null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        action={
          <Button onClick={() => setFormMode("create")}>
            <Plus className="size-4" aria-hidden="true" />
            New Track
          </Button>
        }
        description="Organize study work into long-lived learning goals."
        title="Learning Tracks"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {formMode ? (
        <FormShell
          description="Give this track a clear scope so logs and memories can attach to it later."
          onCancel={closeForm}
          title={formMode === "edit" ? "Edit learning track" : "Create learning track"}
        >
          <LearningTrackForm initialValue={selectedTrack} onCancel={closeForm} onSubmit={handleSubmit} />
        </FormShell>
      ) : null}

      <EntityTable
        columns={[
          {
            header: "Name",
            key: "name",
            render: (track) => <span className="font-medium text-foreground">{track.name}</span>,
          },
          {
            header: "Description",
            key: "description",
            render: (track) => (
              <span className="line-clamp-2 text-muted-foreground">
                {track.description || "No description"}
              </span>
            ),
          },
          {
            header: "Created",
            key: "created",
            render: (track) => new Date(track.created_at).toLocaleDateString(),
          },
          {
            className: "w-28 text-right",
            header: "",
            key: "actions",
            render: (track) => (
              <div className="flex justify-end gap-1">
                <Button
                  aria-label={`Edit ${track.name}`}
                  onClick={() => {
                    setSelectedTrack(track);
                    setFormMode("edit");
                  }}
                  size="icon"
                  variant="ghost"
                >
                  <Edit className="size-4" aria-hidden="true" />
                </Button>
                <Button
                  aria-label={`Delete ${track.name}`}
                  onClick={() => void handleDelete(track)}
                  size="icon"
                  variant="ghost"
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
              </div>
            ),
          },
        ]}
        data={tracks}
        emptyMessage="No learning tracks yet. Create one to start grouping your study work."
        getRowKey={(track) => track.id}
        isLoading={isLoading}
      />
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
