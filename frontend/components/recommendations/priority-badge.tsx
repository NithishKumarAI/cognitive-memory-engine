import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RecommendationPriority } from "@/types/recommendation";

const priorityClasses: Record<RecommendationPriority, string> = {
  high: "border-destructive/40 bg-destructive/10 text-destructive",
  medium: "border-amber-500/40 bg-amber-50 text-amber-700",
  low: "border-emerald-500/40 bg-emerald-50 text-emerald-700",
};

export function PriorityBadge({ priority }: { priority: RecommendationPriority }) {
  return <Badge className={cn("capitalize", priorityClasses[priority])}>{priority}</Badge>;
}
