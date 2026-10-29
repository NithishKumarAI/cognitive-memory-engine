"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";

type AuthGuardProps = {
  children: React.ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, status, refreshUser, edition } = useAuth();

  useEffect(() => {
    if (status === "unauthenticated" && edition === "product") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [pathname, router, status, edition]);

  if (status === "error") return <div role="alert" className="p-8 text-center"><p>We could not verify your session. Your sign-in has been kept.</p><button className="mt-4 rounded-xl bg-primary px-5 py-3 text-primary-foreground" onClick={() => void refreshUser()}>Retry connection</button></div>;

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
      </div>
    );
  }

  return children;
}
