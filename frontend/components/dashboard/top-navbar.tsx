"use client";

import { LogOut, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";

export function TopNavbar() {
  const { logout, user } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex h-16 items-center gap-4 px-4 sm:px-6">
        <div className="relative hidden max-w-md flex-1 md:block">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input className="pl-9" placeholder="Search memories, logs, or tracks" type="search" />
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium">{user?.username ?? "Learner"}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <Button aria-label="Log out" onClick={logout} size="icon" variant="ghost">
            <LogOut className="size-4" aria-hidden="true" />
          </Button>
        </div>
      </div>
    </header>
  );
}
