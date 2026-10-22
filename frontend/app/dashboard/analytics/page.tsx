"use client";
import { errorMessage } from "@/lib/errors";

import { Activity, AlertTriangle, BookMarked, CheckCircle2, Clock, Flame, HelpCircle, Loader2, NotebookText } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/dashboard/chart-card";
import { MetricCard } from "@/components/dashboard/metric-card";
import { PageHeader } from "@/components/dashboard/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getAnalyticsOverview,
  getConsistency,
  getDailyActivity,
  getTopicDistribution,
} from "@/services/analytics";
import { getLearningOverview } from "@/services/learning";
import type {
  AnalyticsOverview,
  Consistency,
  DailyActivityItem,
  TopicDistributionItem,
} from "@/types/analytics";
import type { LearningOverview } from "@/types/continuity";

const chartColors = ["#0f766e", "#2563eb", "#f59e0b", "#dc2626", "#7c3aed", "#059669"];

export default function AnalyticsPage() {
  const [, setConsistency] = useState<Consistency | null>(null);
  const [dailyActivity, setDailyActivity] = useState<DailyActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [learningOverview, setLearningOverview] = useState<LearningOverview | null>(null);
  const [topicDistribution, setTopicDistribution] = useState<TopicDistributionItem[]>([]);

  useEffect(() => {
    async function loadAnalytics() {
      setIsLoading(true);
      setError(null);

      try {
        const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
        const [overviewData, topicData, activityData, consistencyData, learningData] = await Promise.all([
          getAnalyticsOverview(),
          getTopicDistribution(),
          getDailyActivity(),
          getConsistency(),
          getLearningOverview(userTz),
        ]);

        setOverview(overviewData);
        setTopicDistribution(topicData);
        setDailyActivity(activityData);
        setConsistency(consistencyData);
        setLearningOverview(learningData);
      } catch (caughtError) {
        setError(getErrorMessage(caughtError, "Unable to load analytics."));
      } finally {
        setIsLoading(false);
      }
    }

    void loadAnalytics();
  }, []);

  const activityChartData = useMemo(
    () =>
      dailyActivity.map((item) => ({
        date: new Date(`${item.date}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        minutes: item.study_minutes,
      })),
    [dailyActivity],
  );

  const consistencyChartData = useMemo(() => activityChartData.slice(-30), [activityChartData]);

  return (
    <div className="space-y-6">
      <PageHeader
        description="Recorded time and activity, alongside the questions and intentions in your confirmed updates."
        title="A clearer picture of your learning"
      />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <Card className="flex min-h-72 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
        </Card>
      ) : (
        <>
          <h2 className="text-xl font-semibold">Recorded study activity</h2>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              helper={`${overview?.total_topics ?? 0} topics covered`}
              icon={NotebookText}
              label="Total Study Logs"
              value={overview?.total_study_logs ?? 0}
            />
            <MetricCard
              helper="Across all logged sessions"
              icon={Clock}
              label="Logged Study Hours"
              value={(overview?.total_hours ?? 0).toFixed(1)}
            />
            <MetricCard
              helper="Consecutive study days (timezone-aware)"
              icon={Flame}
              label="Current Streak"
              value={`${overview?.current_streak ?? 0} ${overview?.current_streak === 1 ? "day" : "days"}`}
            />
            <MetricCard
              helper="Activity consistency only; not a knowledge score"
              icon={Activity}
              label="Consistency Score"
              value={(overview?.consistency_score ?? 0).toFixed(1)}
            />
          </section>

          {/* Confirmed learning reflections Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Confirmed learning reflections</CardTitle>
              <CardDescription>
                Confirmed observations, self-reported understanding, and learning items needing attention.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-border p-3.5 space-y-1">
                  <div className="flex items-center gap-2 text-primary font-medium text-xs">
                    <BookMarked className="size-4" />
                    <span>Confirmed Captures</span>
                  </div>
                  <p className="text-2xl font-bold">{learningOverview?.confirmed_captures_count ?? 0}</p>
                  <p className="text-xs text-muted-foreground">
                    {learningOverview?.distinct_topics_count ?? 0} distinct topics recorded
                  </p>
                </div>

                <div className="rounded-lg border border-border p-3.5 space-y-1">
                  <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-400 font-medium text-xs">
                    <CheckCircle2 className="size-4" />
                    <span>Understood Self-Reports</span>
                  </div>
                  <p className="text-2xl font-bold">{learningOverview?.understood_count ?? 0}</p>
                  <p className="text-xs text-muted-foreground">
                    Self-reported understanding (not assessed mastery)
                  </p>
                </div>

                <div className="rounded-lg border border-border p-3.5 space-y-1">
                  <div className="flex items-center gap-2 text-destructive font-medium text-xs">
                    <AlertTriangle className="size-4" />
                    <span>Reported Difficulties</span>
                  </div>
                  <p className="text-2xl font-bold">{learningOverview?.unresolved_difficulties_count ?? 0}</p>
                  <p className="text-xs text-muted-foreground">
                    {learningOverview?.difficulties_count ?? 0} total recorded
                  </p>
                </div>

                <div className="rounded-lg border border-border p-3.5 space-y-1">
                  <div className="flex items-center gap-2 text-amber-800 dark:text-amber-400 font-medium text-xs">
                    <HelpCircle className="size-4" />
                    <span>Open Questions</span>
                  </div>
                  <p className="text-2xl font-bold">{learningOverview?.unresolved_questions_count ?? 0}</p>
                  <p className="text-xs text-muted-foreground">
                    {learningOverview?.pending_next_actions_count ?? 0} pending next steps
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Study History and Consistency Charts */}
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard
              description="Actual logged hours by topic. Captures without minutes add no study time."
              title="Topic Distribution" hasData={topicDistribution.length > 0}
            >
              <ResponsiveContainer height="100%" width="100%" initialDimension={{ width: 300, height: 280 }}>
                <PieChart accessibilityLayer>
                  <Pie
                    data={topicDistribution}
                    dataKey="total_hours"
                    innerRadius={58}
                    nameKey="topic"
                    outerRadius={100}
                    paddingAngle={3}
                  >
                    {topicDistribution.map((entry, index) => (
                      <Cell fill={chartColors[index % chartColors.length]} key={entry.topic} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${Number(value).toFixed(1)} h`, "Hours"]} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard description="Minutes studied per active day." title="Daily Activity" hasData={activityChartData.length > 0}>
              <ResponsiveContainer height="100%" width="100%" initialDimension={{ width: 300, height: 280 }}>
                <BarChart data={activityChartData.slice(-30)} accessibilityLayer>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} minTickGap={25} />
                  <YAxis tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <Tooltip formatter={(value) => [`${value} min`, "Study time"]} />
                  <Bar dataKey="minutes" fill="#0f766e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard description="Logged minutes on your latest 30 active dates. This is activity, not mastery." title="Recent study rhythm" hasData={consistencyChartData.length > 0}>
              <ResponsiveContainer height="100%" width="100%" initialDimension={{ width: 300, height: 280 }}>
                <LineChart data={consistencyChartData} accessibilityLayer>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} minTickGap={25} />
                  <YAxis tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "var(--card)", borderColor: "var(--border)", color: "var(--foreground)" }} formatter={value => [`${value} min`, "Logged study time"]} />
                  <Line
                    dataKey="minutes"
                    dot={{ r: 5 }}
                    stroke="#2563eb"
                    strokeWidth={3}
                    type="monotone"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard description="Session volume by topic." title="Topic Sessions" hasData={topicDistribution.length > 0}>
              <ResponsiveContainer height="100%" width="100%" initialDimension={{ width: 300, height: 280 }}>
                <BarChart data={topicDistribution.slice(0, 12)} layout="vertical" accessibilityLayer>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <YAxis dataKey="topic" type="category" tickLine={false} width={110} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <Tooltip formatter={(value) => [`${value}`, "Sessions"]} />
                  <Bar dataKey="session_count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>
        </>
      )}
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return errorMessage(error, fallback);
}
