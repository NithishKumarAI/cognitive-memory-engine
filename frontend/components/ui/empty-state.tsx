import Link from "next/link";
import { BookOpenCheck } from "lucide-react";
export function EmptyState({ title, description, href, action }: { title: string; description: string; href?: string; action?: string }) {
  return <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border px-6 py-10 text-center"><span className="rounded-2xl bg-muted p-3 text-primary"><BookOpenCheck aria-hidden="true" className="size-6" /></span><h3 className="font-semibold">{title}</h3><p className="max-w-sm text-sm text-muted-foreground">{description}</p>{href ? <Link className="mt-1 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground" href={href}>{action ?? "Capture learning"}</Link> : null}</div>;
}
