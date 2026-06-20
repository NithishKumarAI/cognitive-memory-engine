"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpenCheck,
  Brain,
  GraduationCap,
  LayoutDashboard,
  MessageSquareText,
  Sparkles,
} from "lucide-react";

import { cn } from "@/lib/utils";

const sidebarItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/dashboard/learning-tracks", icon: GraduationCap, label: "Learning Tracks" },
  { href: "/dashboard/study-logs", icon: BookOpenCheck, label: "Study Logs" },
  { href: "/dashboard/memories", icon: Brain, label: "Memories" },
  { href: "/dashboard/chat", icon: MessageSquareText, label: "Chat" },
  { href: "/dashboard/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/dashboard/recommendations", icon: Sparkles, label: "Recommendations" },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-72 shrink-0 border-r border-border bg-sidebar px-4 py-5 text-sidebar-foreground lg:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex size-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Brain className="size-5" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold">Cognitive Memory</p>
          <p className="text-xs text-muted-foreground">Engine</p>
        </div>
      </div>

      <nav className="space-y-1" aria-label="Dashboard navigation">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              className={cn(
                "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
              )}
              href={item.href}
              key={item.href}
            >
              <Icon className="size-4" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
