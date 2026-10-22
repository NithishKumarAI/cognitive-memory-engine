"use client";
import { errorMessage } from "@/lib/errors";

import Link from "next/link";
import { Edit, Eye, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useConfirmDialog } from "@/components/ui/confirm-dialog";
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
  const { confirm, dialog } = useConfirmDialog();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
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
    try {
    if (formMode === "edit" && selectedMemory) {
      await updateMemory(selectedMemory.id, payload);
    } else {
      await createMemory(payload);
    }

    closeForm();
    await loadData();
    } catch (error) { setError(getErrorMessage(error, "Unable to save. Check your input and retry.")); }
  }

  async function handleDelete(memory: Memory) {
    const confirmed = await confirm(`Delete memory “${memory.title}”? Its original capture, if any, remains in your learning history.`);

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

      <div className="flex flex-col gap-3 sm:flex-row"><Input aria-label="Filter memories" placeholder="Find a memory in this view…" value={query} onChange={event => setQuery(event.target.value)} /><select aria-label="Filter category" className="min-h-11 rounded-xl border border-input bg-card px-3 text-sm" value={category} onChange={event => setCategory(event.target.value)}><option value="">All categories</option>{[...new Set(memories.map(memory => memory.category))].map(value => <option key={value}>{value}</option>)}</select></div>
      {isLoading ? <Skeleton /> : memories.filter(memory => (!category || memory.category === category) && `${memory.title} ${memory.content}`.toLowerCase().includes(query.toLowerCase())).length ? <div className="grid gap-4 md:grid-cols-2">{memories.filter(memory => (!category || memory.category === category) && `${memory.title} ${memory.content}`.toLowerCase().includes(query.toLowerCase())).map(memory => <Card className="flex flex-col p-6" key={memory.id}><Badge className="self-start">{memory.category}</Badge><Link className="mt-4 text-lg font-semibold hover:text-primary" href={`/dashboard/memories/${memory.id}`}>{memory.title}</Link><p className="mt-3 line-clamp-4 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{memory.content}</p>{memory.study_log_id ? <Link className="mt-4 min-h-11 text-xs text-primary" href={`/dashboard/study-logs#record-${memory.study_log_id}`}>Study log: {studyLogTopic(memory.study_log_id)}</Link> : <p className="mt-4 text-xs text-muted-foreground">No linked timed session</p>}<div className="mt-auto flex flex-wrap gap-2 pt-5"><Button asChild variant="secondary"><Link href={`/dashboard/memories/${memory.id}`}><Eye aria-hidden="true" />Read memory</Link></Button><Button variant="ghost" aria-label={`Edit ${memory.title}`} onClick={() => { setSelectedMemory(memory); setFormMode("edit"); }}><Edit aria-hidden="true" />Edit</Button><Button variant="ghost" aria-label={`Delete ${memory.title}`} onClick={() => void handleDelete(memory)}><Trash2 aria-hidden="true" />Delete</Button></div></Card>)}</div> : <EmptyState title={memories.length ? "No matching memories" : "Keep what you want to remember"} description="Save a memory manually or opt into searchable memories when you confirm a capture." href="/dashboard/capture" />}
      {dialog}
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return errorMessage(error, fallback);
}
