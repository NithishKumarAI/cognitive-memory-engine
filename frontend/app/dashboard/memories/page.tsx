"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { Edit, Eye, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { EntityTable } from "@/components/dashboard/entity-table";
import { FormShell } from "@/components/dashboard/form-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { MemoryForm } from "@/components/forms/memory-form";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createMemory, deleteMemory, listMemories, updateMemory } from "@/services/memories";
import { listStudyLogs } from "@/services/studyLogs";
import type { Memory, MemoryPayload } from "@/types/memory";
import type { StudyLog } from "@/types/studyLog";

export default function MemoriesPage() {
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [studyLogs, setStudyLogs] = useState<StudyLog[]>([]);

  async function loadData() {
    setIsLoading(true);
    setError(null);

    try {
      const [logs, memoryList] = await Promise.all([listStudyLogs(), listMemories()]);
      setStudyLogs(logs);
      setMemories(memoryList);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to load memories."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // Page data is loaded from the API when this protected client route mounts.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadData();
  }, []);

  async function handleSubmit(payload: MemoryPayload) {
    if (formMode === "edit" && selectedMemory) {
      await updateMemory(selectedMemory.id, payload);
    } else {
      await createMemory(payload);
    }

    closeForm();
    await loadData();
  }

  async function handleDelete(memory: Memory) {
    const confirmed = window.confirm(`Delete memory "${memory.title}"?`);

    if (!confirmed) {
      return;
    }

    try {
      await deleteMemory(memory.id);
      await loadData();
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to delete memory."));
    }
  }

  function closeForm() {
    setFormMode(null);
    setSelectedMemory(null);
  }

  function studyLogTopic(logId: number | null) {
    return studyLogs.find((log) => log.id === logId)?.topic ?? "No study log";
  }

  return (
    <div className="space-y-6">
      <PageHeader
        action={
          <Button onClick={() => setFormMode("create")}>
            <Plus className="size-4" aria-hidden="true" />
            New Memory
          </Button>
        }
        description="Store durable knowledge snippets that can power retrieval and chat answers."
        title="Memories"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {formMode ? (
        <FormShell
          description="Write a concise memory with enough context for future retrieval."
          onCancel={closeForm}
          title={formMode === "edit" ? "Edit memory" : "Create memory"}
        >
          <MemoryForm
            initialValue={selectedMemory}
            onCancel={closeForm}
            onSubmit={handleSubmit}
            studyLogs={studyLogs}
          />
        </FormShell>
      ) : null}

      <EntityTable
        columns={[
          {
            header: "Title",
            key: "title",
            render: (memory) => <span className="font-medium text-foreground">{memory.title}</span>,
          },
          {
            header: "Category",
            key: "category",
            render: (memory) => <Badge>{memory.category}</Badge>,
          },
          {
            header: "Study Log",
            key: "studyLog",
            render: (memory) => (
              <span className="text-muted-foreground">{studyLogTopic(memory.study_log_id)}</span>
            ),
          },
          {
            header: "Content",
            key: "content",
            render: (memory) => (
              <span className="line-clamp-2 text-muted-foreground">{memory.content}</span>
            ),
          },
          {
            className: "w-36 text-right",
            header: "",
            key: "actions",
            render: (memory) => (
              <div className="flex justify-end gap-1">
                <Button aria-label={`View ${memory.title}`} asChild size="icon" variant="ghost">
                  <Link href={`/dashboard/memories/${memory.id}`}>
                    <Eye className="size-4" aria-hidden="true" />
                  </Link>
                </Button>
                <Button
                  aria-label={`Edit ${memory.title}`}
                  onClick={() => {
                    setSelectedMemory(memory);
                    setFormMode("edit");
                  }}
                  size="icon"
                  variant="ghost"
                >
                  <Edit className="size-4" aria-hidden="true" />
                </Button>
                <Button
                  aria-label={`Delete ${memory.title}`}
                  onClick={() => void handleDelete(memory)}
                  size="icon"
                  variant="ghost"
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
              </div>
            ),
          },
        ]}
        data={memories}
        emptyMessage="No memories yet. Create one from an insight you want to keep."
        getRowKey={(memory) => memory.id}
        isLoading={isLoading}
      />
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
