"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { ArrowRight, BookOpenCheck, Brain, Calendar, CheckCircle2, GraduationCap, HelpCircle, Loader2, PlayCircle, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { MetricCard } from "@/components/dashboard/metric-card";
import { PageHeader } from "@/components/dashboard/page-header";
import { PriorityBadge } from "@/components/recommendations/priority-badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listLearningTracks } from "@/services/learningTracks";
import { listMemories } from "@/services/memories";
import { listStudyLogs } from "@/services/studyLogs";
import { getCheckpoints, getLearningRecommendations } from "@/services/learning";
import type { ResumableCheckpoint, EvidenceRecommendation } from "@/types/continuity";

export default function DashboardPage() {
  const [counts, setCounts] = useState({
    memories: 0,
    recommendations: 0,
    studyLogs: 0,
    tracks: 0,
  });
  const [checkpoints, setCheckpoints] = useState<ResumableCheckpoint[]>([]);
  const [recommendations, setRecommendations] = useState<EvidenceRecommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setError(null);

      try {
        const [tracks, studyLogs, memories, cpData, recData] = await Promise.all([
          listLearningTracks(),
          listStudyLogs(),
          listMemories(),
          getCheckpoints(undefined, 3),
          getLearningRecommendations(5),
        ]);

        setCounts({
          memories: memories.length,
          recommendations: recData.length,
          studyLogs: studyLogs.length,
          tracks: tracks.length,
        });
        setCheckpoints(cpData);
        setRecommendations(recData);
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, "Unable to load dashboard summary."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const metrics = [
    { icon: GraduationCap, label: "Active Tracks", value: counts.tracks },
    { icon: BookOpenCheck, label: "Study Logs", value: counts.studyLogs },
    { icon: Brain, label: "Stored Memories", value: counts.memories },
    { icon: Sparkles, label: "Recommendations", value: counts.recommendations },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <PageHeader
          description="Your learning continuity, where you left off, and evidence-based recommendations."
          title="Dashboard"
        />
        <Link
          href="/dashboard/capture"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <PlayCircle className="size-4" aria-hidden="true" />
          Capture Learning
        </Link>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            value={
              isLoading ? (
                <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
              ) : (
                metric.value
              )
            }
          />
        ))}
      </section>

      {/* Continue where you left off */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Continue Where You Left Off</CardTitle>
            <CardDescription>
              Resumable checkpoints reconstructed from your confirmed learning updates.
            </CardDescription>
          </div>
          <Link
            href="/dashboard/capture"
            className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
          >
            All captures <ArrowRight className="size-3" aria-hidden="true" />
          </Link>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex min-h-36 items-center justify-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : checkpoints.length === 0 ? (
            <div className="flex min-h-36 flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
              <p className="font-medium text-foreground">No learning checkpoints recorded yet.</p>
              <p className="text-xs">
                Capture what you study today, confirm your observations, and pick up right where you left off.
              </p>
              <Link
                href="/dashboard/capture"
                className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                Capture your first update <ArrowRight className="size-3" />
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {checkpoints.map((cp) => (
                <Card className="shadow-none border border-border" key={`${cp.topic}-${cp.learning_track_id}`}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <CardTitle className="text-base">{cp.topic}</CardTitle>
                        {cp.learning_track_name ? (
                          <p className="text-xs text-muted-foreground mt-0.5">Track: {cp.learning_track_name}</p>
                        ) : null}
                      </div>
                      <Badge className={cp.state === "needs_attention" ? "bg-destructive/15 text-destructive border-destructive/20 capitalize" : "capitalize"}>
                        {cp.state.replace(/_/g, " ")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    {cp.last_capture_excerpt ? (
                      <p className="text-muted-foreground italic line-clamp-2">
                        &quot;{cp.last_capture_excerpt}&quot;
                      </p>
                    ) : null}

                    <div className="space-y-1.5 border-t border-border pt-2 text-muted-foreground">
                      {cp.unresolved_difficulties.length > 0 ? (
                        <p className="flex items-center gap-1.5 text-destructive font-medium">
                          <HelpCircle className="size-3.5 shrink-0" />
                          {cp.unresolved_difficulties.length} difficulty recorded
                        </p>
                      ) : null}
                      {cp.pending_next_steps.length > 0 ? (
                        <p className="flex items-center gap-1.5 text-primary font-medium">
                          <CheckCircle2 className="size-3.5 shrink-0" />
                          {cp.pending_next_steps.length} intended next step pending
                        </p>
                      ) : null}
                      <p className="flex items-center gap-1.5 text-muted-foreground">
                        <Calendar className="size-3.5 shrink-0" />
                        {cp.days_since_last_activity === 0
                          ? "Studied today"
                          : `${cp.days_since_last_activity} day${cp.days_since_last_activity > 1 ? "s" : ""} ago`}
                      </p>
                    </div>

                    <div className="pt-1 flex items-center justify-between">
                      {cp.last_capture_id ? (
                        <Link
                          href="/dashboard/capture"
                          className="text-xs text-primary font-medium hover:underline inline-flex items-center gap-1"
                        >
                          Capture #{cp.last_capture_id} <ArrowRight className="size-3" />
                        </Link>
                      ) : null}
                      {cp.learning_track_id ? (
                        <Link
                          href="/dashboard/learning-tracks"
                          className="text-xs text-muted-foreground hover:underline"
                        >
                          View track
                        </Link>
                      ) : null}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommended next actions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Evidence-Based Recommendations</CardTitle>
            <CardDescription>
              Prioritized actions derived from your confirmed notes, difficulties, and plans.
            </CardDescription>
          </div>
          <Link
            href="/dashboard/recommendations"
            className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
          >
            All recommendations <ArrowRight className="size-3" aria-hidden="true" />
          </Link>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex min-h-24 items-center justify-center">
              <Loader2 className="size-5 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : recommendations.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              No recommendations currently pending. Keep recording your learning updates!
            </p>
          ) : (
            <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec) => (
                <div
                  key={rec.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-md border border-border p-3.5"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <PriorityBadge priority={rec.priority} />
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        {rec.topic}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-foreground">{rec.action}</p>
                    <p className="text-xs text-muted-foreground">{rec.reason}</p>
                  </div>
                  <div className="shrink-0 flex items-center gap-2">
                    <Link
                      href="/dashboard/recommendations"
                      className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                    >
                      View & Resolve <ArrowRight className="size-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
