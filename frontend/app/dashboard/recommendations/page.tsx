"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { ArrowRight, CalendarClock, Check, EyeOff, Loader2, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/dashboard/page-header";
import { PriorityBadge } from "@/components/recommendations/priority-badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDailyRecommendations } from "@/services/recommendations";
import { recordLearningAction } from "@/services/learning";
import type { DailyRecommendations, Recommendation } from "@/types/recommendation";

const priorityOrder = {
  high: 0,
  medium: 1,
  low: 2,
};

export default function RecommendationsPage() {
  const [dailyFeed, setDailyFeed] = useState<DailyRecommendations | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function fetchRecommendations() {
      setIsLoading(true);
      setError(null);
      try {
        const feed = await getDailyRecommendations();
        if (isMounted) {
          setDailyFeed(feed);
        }
      } catch (caughtError) {
        if (isMounted) {
          setError(getErrorMessage(caughtError, "Unable to load recommendations."));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void fetchRecommendations();

    return () => {
      isMounted = false;
    };
  }, [refreshTrigger]);

  const recommendations = useMemo(
    () =>
      [...(dailyFeed?.recommendations ?? [])].sort(
        (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority],
      ),
    [dailyFeed],
  );

  async function handleAction(rec: Recommendation, status: "completed" | "dismissed") {
    const key = `action-${rec.id ?? rec.type}-${crypto.randomUUID()}`;
    setActionLoadingId(rec.id ?? rec.type);
    setActionSuccess(null);
    setError(null);

    let actionType: "next_step" | "difficulty" | "question" | "review" | "recommendation" = "recommendation";
    if (rec.type === "intended_next_step") actionType = "next_step";
    else if (rec.type === "unresolved_difficulty") actionType = "difficulty";
    else if (rec.type === "open_question") actionType = "question";
    else if (rec.type === "review_suggestion") actionType = "review";

    try {
      await recordLearningAction({
        idempotency_key: key,
        action_type: actionType,
        status,
        observation_id: rec.source_observation_id ?? undefined,
        capture_id: rec.source_capture_id ?? undefined,
        learning_track_id: rec.learning_track_id ?? undefined,
        topic: rec.topic ?? undefined,
        recommendation_id: rec.id ?? undefined,
      });

      setActionSuccess(
        status === "completed"
          ? `Marked "${rec.topic ?? rec.action}" action as completed.`
          : `Dismissed recommendation for "${rec.topic ?? rec.action}".`
      );
      setRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to record action. Please retry."));
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        description="Evidence-based recommendations derived from confirmed notes, difficulties, and learning checkpoints."
        title="Recommendations"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {actionSuccess ? (
        <Alert>
          <AlertDescription className="text-sm text-foreground">{actionSuccess}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Daily Recommendation Feed</CardTitle>
            <CardDescription>
              {dailyFeed
                ? `Generated ${new Date(dailyFeed.generated_at).toLocaleString()}`
                : "Generated from the latest confirmed learning evidence."}
            </CardDescription>
          </div>
          <Badge className="gap-1">
            <CalendarClock className="size-3" aria-hidden="true" />
            Evidence-Based
          </Badge>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex min-h-56 items-center justify-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : null}

          {!isLoading && recommendations.length === 0 ? (
            <div className="flex min-h-56 flex-col items-center justify-center gap-2 text-center text-sm text-muted-foreground">
              <Sparkles className="size-8 text-muted-foreground/60" />
              <p className="font-medium text-foreground">All caught up!</p>
              <p className="text-xs">
                No pending next steps, unresolved difficulties, or review suggestions at this time.
              </p>
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recommendations.map((recommendation, index) => {
              const recKey = recommendation.id ?? `${recommendation.type}-${index}`;
              const isBusy = actionLoadingId === (recommendation.id ?? recommendation.type);

              return (
                <Card className="shadow-none border border-border flex flex-col justify-between" key={recKey}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                        <Sparkles className="size-5" aria-hidden="true" />
                      </div>
                      <PriorityBadge priority={recommendation.priority} />
                    </div>
                    {recommendation.topic ? (
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mt-1">
                        {recommendation.topic}
                      </p>
                    ) : null}
                    <CardTitle className="text-base font-semibold">
                      {recommendation.action ?? recommendation.type.replaceAll("_", " ")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    <p className="text-xs leading-5 text-muted-foreground">
                      {recommendation.reason ?? recommendation.message}
                    </p>

                    {recommendation.evidence ? (
                      <div className="rounded bg-muted p-2 text-xs italic text-muted-foreground line-clamp-2">
                        &quot;{recommendation.evidence}&quot;
                      </div>
                    ) : null}

                    {recommendation.source_capture_id ? (
                      <div className="pt-1">
                        <Link
                          href="/dashboard/capture"
                          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          Source: Capture #{recommendation.source_capture_id} <ArrowRight className="size-3" />
                        </Link>
                      </div>
                    ) : null}

                    <div className="flex items-center gap-2 pt-2 border-t border-border">
                      <Button
                        size="sm"
                        variant="default"
                        className="text-xs h-8 gap-1.5 flex-1"
                        disabled={isBusy}
                        onClick={() => handleAction(recommendation, "completed")}
                      >
                        {isBusy ? <Loader2 className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
                        Complete
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-8 gap-1.5"
                        disabled={isBusy}
                        onClick={() => handleAction(recommendation, "dismissed")}
                      >
                        <EyeOff className="size-3.5" />
                        Dismiss
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
