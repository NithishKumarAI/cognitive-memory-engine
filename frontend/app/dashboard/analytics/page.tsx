"use client";

import { AxiosError } from "axios";
import { Activity, Clock, Flame, Loader2, NotebookText } from "lucide-react";
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
import { Card } from "@/components/ui/card";
import {
  getAnalyticsOverview,
  getConsistency,
  getDailyActivity,
  getTopicDistribution,
} from "@/services/analytics";
import type {
  AnalyticsOverview,
  Consistency,
  DailyActivityItem,
  TopicDistributionItem,
} from "@/types/analytics";

const chartColors = ["#0f766e", "#2563eb", "#f59e0b", "#dc2626", "#7c3aed", "#059669"];

export default function AnalyticsPage() {
  const [consistency, setConsistency] = useState<Consistency | null>(null);
  const [dailyActivity, setDailyActivity] = useState<DailyActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [topicDistribution, setTopicDistribution] = useState<TopicDistributionItem[]>([]);

  useEffect(() => {
    async function loadAnalytics() {
      setIsLoading(true);
      setError(null);

      try {
        const [overviewData, topicData, activityData, consistencyData] = await Promise.all([
          getAnalyticsOverview(),
          getTopicDistribution(),
          getDailyActivity(),
          getConsistency(),
        ]);

        setOverview(overviewData);
        setTopicDistribution(topicData);
        setDailyActivity(activityData);
        setConsistency(consistencyData);
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
        date: new Date(item.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        minutes: item.study_minutes,
      })),
    [dailyActivity],
  );

  const consistencyChartData = useMemo(
    () => [
      { label: "Current Streak", value: consistency?.current_streak ?? 0 },
      { label: "Frequency", value: consistency?.frequency_percentage ?? 0 },
      { label: "Score", value: consistency?.consistency_score ?? 0 },
    ],
    [consistency],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        description="Review study volume, topic focus, daily activity, and consistency."
        title="Analytics"
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
              label="Total Hours"
              value={(overview?.total_hours ?? 0).toFixed(1)}
            />
            <MetricCard
              helper="Consecutive study days"
              icon={Flame}
              label="Current Streak"
              value={`${overview?.current_streak ?? 0} days`}
            />
            <MetricCard
              helper="Weighted activity score"
              icon={Activity}
              label="Consistency Score"
              value={(overview?.consistency_score ?? 0).toFixed(1)}
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard
              description="Total hours by topic, weighted by session count."
              title="Topic Distribution"
            >
              <ResponsiveContainer height="100%" width="100%">
                <PieChart>
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

            <ChartCard description="Minutes studied per active day." title="Daily Activity">
              <ResponsiveContainer height="100%" width="100%">
                <BarChart data={activityChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} />
                  <YAxis tickLine={false} />
                  <Tooltip formatter={(value) => [`${value} min`, "Study time"]} />
                  <Bar dataKey="minutes" fill="#0f766e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard description="Streak, study frequency, and consistency score." title="Consistency">
              <ResponsiveContainer height="100%" width="100%">
                <LineChart data={consistencyChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tickLine={false} />
                  <YAxis tickLine={false} />
                  <Tooltip />
                  <Line
                    dataKey="value"
                    dot={{ r: 5 }}
                    stroke="#2563eb"
                    strokeWidth={3}
                    type="monotone"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard description="Session volume by topic." title="Topic Sessions">
              <ResponsiveContainer height="100%" width="100%">
                <BarChart data={topicDistribution} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickLine={false} />
                  <YAxis dataKey="topic" type="category" tickLine={false} width={110} />
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
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
