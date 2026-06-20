"use client";

import { AxiosError } from "axios";
import { Edit, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { EntityTable } from "@/components/dashboard/entity-table";
import { FormShell } from "@/components/dashboard/form-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { StudyLogForm } from "@/components/forms/study-log-form";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listLearningTracks } from "@/services/learningTracks";
import { createStudyLog, deleteStudyLog, listStudyLogs, updateStudyLog } from "@/services/studyLogs";
import type { LearningTrack } from "@/types/learningTrack";
import type { StudyLog, StudyLogPayload } from "@/types/studyLog";

export default function StudyLogsPage() {
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [learningTracks, setLearningTracks] = useState<LearningTrack[]>([]);
  const [selectedLog, setSelectedLog] = useState<StudyLog | null>(null);
  const [studyLogs, setStudyLogs] = useState<StudyLog[]>([]);

  async function loadData() {
    setIsLoading(true);
    setError(null);

    try {
      const [tracks, logs] = await Promise.all([listLearningTracks(), listStudyLogs()]);
      setLearningTracks(tracks);
      setStudyLogs(logs);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to load study logs."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // Page data is loaded from the API when this protected client route mounts.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadData();
  }, []);

  async function handleSubmit(payload: StudyLogPayload) {
    if (formMode === "edit" && selectedLog) {
      await updateStudyLog(selectedLog.id, payload);
    } else {
      await createStudyLog(payload);
    }

    closeForm();
    await loadData();
  }

  async function handleDelete(log: StudyLog) {
    const confirmed = window.confirm(`Delete study log "${log.topic}"?`);

    if (!confirmed) {
      return;
    }

    try {
      await deleteStudyLog(log.id);
      await loadData();
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to delete study log."));
    }
  }

  function closeForm() {
    setFormMode(null);
    setSelectedLog(null);
  }

  function trackName(trackId: number | null) {
    return learningTracks.find((track) => track.id === trackId)?.name ?? "No track";
  }

  return (
    <div className="space-y-6">
      <PageHeader
        action={
          <Button onClick={() => setFormMode("create")}>
            <Plus className="size-4" aria-hidden="true" />
            New Log
          </Button>
        }
        description="Capture study sessions, durations, notes, and their related track."
        title="Study Logs"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {formMode ? (
        <FormShell
          description="Log what you studied and the context worth remembering."
          onCancel={closeForm}
          title={formMode === "edit" ? "Edit study log" : "Create study log"}
        >
          <StudyLogForm
            initialValue={selectedLog}
            learningTracks={learningTracks}
            onCancel={closeForm}
            onSubmit={handleSubmit}
          />
        </FormShell>
      ) : null}

      <EntityTable
        columns={[
          {
            header: "Topic",
            key: "topic",
            render: (log) => <span className="font-medium text-foreground">{log.topic}</span>,
          },
          {
            header: "Track",
            key: "track",
            render: (log) => <Badge>{trackName(log.learning_track_id)}</Badge>,
          },
          {
            header: "Duration",
            key: "duration",
            render: (log) => `${log.duration_minutes} min`,
          },
          {
            header: "Notes",
            key: "notes",
            render: (log) => <span className="line-clamp-2 text-muted-foreground">{log.notes}</span>,
          },
          {
            header: "Created",
            key: "created",
            render: (log) => new Date(log.created_at).toLocaleDateString(),
          },
          {
            className: "w-28 text-right",
            header: "",
            key: "actions",
            render: (log) => (
              <div className="flex justify-end gap-1">
                <Button
                  aria-label={`Edit ${log.topic}`}
                  onClick={() => {
                    setSelectedLog(log);
                    setFormMode("edit");
                  }}
                  size="icon"
                  variant="ghost"
                >
                  <Edit className="size-4" aria-hidden="true" />
                </Button>
                <Button
                  aria-label={`Delete ${log.topic}`}
                  onClick={() => void handleDelete(log)}
                  size="icon"
                  variant="ghost"
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
              </div>
            ),
          },
        ]}
        data={studyLogs}
        emptyMessage="No study logs yet. Add one after a focused session."
        getRowKey={(log) => log.id}
        isLoading={isLoading}
      />
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
