import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const metrics = [
  { label: "Active Tracks", value: "0" },
  { label: "Study Logs", value: "0" },
  { label: "Stored Memories", value: "0" },
  { label: "Recommendations", value: "0" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-foreground">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your learning activity, memories, and recommendations will appear here.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="pb-2">
              <CardDescription>{metric.label}</CardDescription>
              <CardTitle className="text-3xl">{metric.value}</CardTitle>
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
