"use client";

import { AxiosError } from "axios";
import { CalendarClock, Loader2, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/dashboard/page-header";
import { PriorityBadge } from "@/components/recommendations/priority-badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDailyRecommendations } from "@/services/recommendations";
import type { DailyRecommendations } from "@/types/recommendation";

const priorityOrder = {
  high: 0,
  medium: 1,
  low: 2,
};

export default function RecommendationsPage() {
  const [dailyFeed, setDailyFeed] = useState<DailyRecommendations | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadRecommendations() {
      setIsLoading(true);
      setError(null);

      try {
        setDailyFeed(await getDailyRecommendations());
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, "Unable to load recommendations."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadRecommendations();
  }, []);

  const recommendations = useMemo(
    () =>
      [...(dailyFeed?.recommendations ?? [])].sort(
        (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority],
      ),
    [dailyFeed],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        description="Daily guidance based on study history, neglected topics, and learning continuity."
        title="Recommendations"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Daily Recommendation Feed</CardTitle>
            <CardDescription>
              {dailyFeed
                ? `Generated ${new Date(dailyFeed.generated_at).toLocaleString()}`
                : "Generated from the latest available learning signals."}
            </CardDescription>
          </div>
          <Badge className="gap-1">
            <CalendarClock className="size-3" aria-hidden="true" />
            Today
          </Badge>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex min-h-56 items-center justify-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : null}

          {!isLoading && recommendations.length === 0 ? (
            <div className="flex min-h-56 items-center justify-center text-center text-sm text-muted-foreground">
              No recommendations available yet.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recommendations.map((recommendation, index) => (
              <Card className="shadow-none" key={`${recommendation.type}-${index}`}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Sparkles className="size-5" aria-hidden="true" />
                    </div>
                    <PriorityBadge priority={recommendation.priority} />
                  </div>
                  <CardTitle className="text-lg capitalize">{recommendation.type.replaceAll("_", " ")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-muted-foreground">{recommendation.message}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
