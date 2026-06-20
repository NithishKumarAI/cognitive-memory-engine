import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ChartCardProps = {
  children: React.ReactNode;
  description: string;
  title: string;
};

export function ChartCard({ children, description, title }: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="h-80">{children}</CardContent>
    </Card>
  );
}
