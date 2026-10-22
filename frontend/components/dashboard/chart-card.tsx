import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ChartCardProps = {
  children: React.ReactNode;
  description: string;
  title: string;
  hasData?: boolean;
};

export function ChartCard({ children, description, title, hasData = true }: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="h-80 min-w-0" role="group" aria-label={`${title}: ${description}`}>{hasData ? children : <p className="flex h-full items-center justify-center text-center text-sm text-muted-foreground">No study sessions recorded yet. Add a study log to see this chart.</p>}</CardContent>
    </Card>
  );
}
