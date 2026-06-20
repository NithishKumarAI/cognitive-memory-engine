import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type MetricCardProps = {
  icon: LucideIcon;
  label: string;
  value: React.ReactNode;
  helper?: string;
};

export function MetricCard({ helper, icon: Icon, label, value }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold text-foreground">{value}</div>
        {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
      </CardContent>
    </Card>
  );
}
