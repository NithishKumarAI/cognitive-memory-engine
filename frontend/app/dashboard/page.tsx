"use client";

import { AxiosError } from "axios";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/dashboard/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listLearningTracks } from "@/services/learningTracks";
import { listMemories } from "@/services/memories";
import { listStudyLogs } from "@/services/studyLogs";

export default function DashboardPage() {
  const [counts, setCounts] = useState({
    memories: 0,
    recommendations: 0,
    studyLogs: 0,
    tracks: 0,
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadCounts() {
      setIsLoading(true);
      setError(null);

      try {
        const [tracks, studyLogs, memories] = await Promise.all([
          listLearningTracks(),
          listStudyLogs(),
          listMemories(),
        ]);

        setCounts({
          memories: memories.length,
          recommendations: 0,
          studyLogs: studyLogs.length,
          tracks: tracks.length,
        });
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, "Unable to load dashboard summary."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadCounts();
  }, []);

  const metrics = [
    { label: "Active Tracks", value: counts.tracks },
    { label: "Study Logs", value: counts.studyLogs },
    { label: "Stored Memories", value: counts.memories },
    { label: "Recommendations", value: counts.recommendations },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        description="Your learning activity, memories, and recommendations at a glance."
        title="Dashboard"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="pb-2">
              <CardDescription>{metric.label}</CardDescription>
              <CardTitle className="text-3xl">
                {isLoading ? (
                  <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
                ) : (
                  metric.value
                )}
              </CardTitle>
            </CardHeader>
          </Card>
        ))}
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Memory Workspace</CardTitle>
          <CardDescription>
            Connect learning tracks, study logs, chat context, and analytics as backend features mature.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="min-h-56 rounded-md border border-dashed border-border bg-background" />
        </CardContent>
      </Card>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
