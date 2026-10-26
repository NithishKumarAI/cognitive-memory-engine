"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenCheck, Brain, GraduationCap, House, MessageSquareText, ChartNoAxesCombined, Compass, History, NotebookPen } from "lucide-react";
import { branding } from "@/lib/branding";
import { cn } from "@/lib/utils";
const items = [
  { href: "/dashboard", label: "Home", icon: House },
  { href: "/dashboard/capture", label: "Capture Learning", icon: NotebookPen },
  { href: "/dashboard/learning-tracks", label: "Learning Paths", icon: GraduationCap },
  { href: "/dashboard/recommendations", label: "Next Actions", icon: Compass },
  { href: "/dashboard/chat", label: "Assistant", icon: MessageSquareText },
  { href: "/dashboard/analytics", label: "Insights", icon: ChartNoAxesCombined },
  { href: "/dashboard/history", label: "Learning History", icon: History },
  { href: "/dashboard/memories", label: "Memory", icon: Brain },
  { href: "/dashboard/study-logs", label: "Study Logs", icon: BookOpenCheck },
];
export function WorkspaceNavigation({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return <><Link onClick={onNavigate} href="/dashboard" className="mb-10 flex items-center gap-3 px-3 py-2"><span className="rounded-2xl bg-primary p-2.5 text-primary-foreground"><Brain className="size-5" aria-hidden="true" /></span><span className="text-sm font-semibold leading-snug">{branding.name}<span className="mt-1 block text-xs font-normal text-muted-foreground">{branding.description}</span></span></Link><nav aria-label="Workspace navigation" className="space-y-1.5">{items.map((item, index) => { const active = item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href); const Icon = item.icon; return <div key={item.href}>{index === 6 ? <p className="mb-3 mt-8 px-4 text-[11px] font-semibold uppercase tracking-[.16em] text-muted-foreground">Your library</p> : null}<Link onClick={onNavigate} aria-current={active ? "page" : undefined} href={item.href} className={cn("flex min-h-11 items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground", active && "bg-sidebar-accent text-sidebar-accent-foreground")}><Icon className="size-[18px]" aria-hidden="true" />{item.label}{active ? <span className="ml-auto size-1.5 rounded-full bg-current" /> : null}</Link></div>; })}</nav><div className="mt-10 rounded-2xl border border-border p-4 text-xs text-muted-foreground"><p className="font-semibold text-foreground">A little learning, remembered.</p><p className="mt-1">Your notes are a place to return to, not a score to chase.</p></div></>;
}
export function DashboardSidebar() { return <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 overflow-y-auto border-r border-border bg-sidebar p-4 xl:w-72 lg:block"><WorkspaceNavigation /></aside>; }
