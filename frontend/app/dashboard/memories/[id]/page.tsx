"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/dashboard/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getMemory } from "@/services/memories";
import type { Memory } from "@/types/memory";

export default function MemoryDetailPage() {
  const params = useParams<{ id: string }>();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [memory, setMemory] = useState<Memory | null>(null);

  useEffect(() => {
    async function loadMemory() {
      setIsLoading(true);
      setError(null);

      try {
        setMemory(await getMemory(Number(params.id)));
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, "Unable to load memory."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadMemory();
  }, [params.id]);

  return (
    <div className="space-y-6">
      <PageHeader
        action={
          <Button asChild variant="outline">
            <Link href="/dashboard/memories">
              <ArrowLeft className="size-4" aria-hidden="true" />
              Back
            </Link>
          </Button>
        }
        description="Inspect the complete stored memory and its linked context."
        title="Memory Detail"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <Card className="flex min-h-64 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
        </Card>
      ) : null}

      {memory ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{memory.category}</Badge>
              {memory.study_log_id ? <Badge>Study log #{memory.study_log_id}</Badge> : null}
            </div>
            <CardTitle>{memory.title}</CardTitle>
            <CardDescription>Memory #{memory.id}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-7 text-foreground">{memory.content}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
