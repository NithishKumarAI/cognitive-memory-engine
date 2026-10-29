"use client";
import Link from "next/link";
import { LogOut, Menu, Search, X } from "lucide-react";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { ThemeControl } from "./theme-control";
import { WorkspaceNavigation } from "./sidebar";
export function TopNavbar() {
  const { logout, user, edition } = useAuth(); const drawer = useRef<HTMLDialogElement>(null); const router = useRouter(); const [query, setQuery] = useState("");
  return <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur"><a href="#main-content" className="skip-link">Skip to content</a><div className="flex h-20 min-w-0 items-center gap-2 px-4 sm:gap-4 sm:px-8">
    <Button className="lg:hidden" variant="ghost" size="icon" aria-label="Open navigation" onClick={() => drawer.current?.showModal()}><Menu aria-hidden="true" /></Button>
    <form role="search" className="relative hidden min-w-0 max-w-lg flex-1 md:block" onSubmit={event => { event.preventDefault(); router.push(`/dashboard/search?q=${encodeURIComponent(query.trim())}`); }}><Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3.5 size-4 text-muted-foreground" /><Input aria-label="Search your learning" minLength={2} maxLength={120} required className="border-transparent bg-muted/70 pl-10 shadow-none" placeholder="Find a thought, topic, or learning moment…" type="search" value={query} onChange={event => setQuery(event.target.value)} /></form>
    <Link aria-label="Search your learning" href="/dashboard/search" className="flex size-11 shrink-0 items-center justify-center rounded-xl hover:bg-muted md:hidden"><Search aria-hidden="true" className="size-5" /></Link><div className="ml-auto flex min-w-0 items-center gap-2 sm:gap-4"><ThemeControl /><div className="hidden max-w-44 truncate text-right text-sm sm:block"><p className="truncate font-medium">{user?.username ?? "Your workspace"}</p><p className="text-xs text-muted-foreground">{edition === "demo" ? "Temporary demo space" : "Personal learning space"}</p></div>{edition === "product" ? <Button aria-label="Log out" onClick={logout} size="icon" variant="ghost"><LogOut aria-hidden="true" /></Button> : null}</div></div>
    <dialog ref={drawer} data-drawer aria-label="Navigation menu"><div className="mb-3 flex justify-end"><Button aria-label="Close navigation" variant="ghost" size="icon" onClick={() => drawer.current?.close()}><X aria-hidden="true" /></Button></div><WorkspaceNavigation onNavigate={() => drawer.current?.close()} /></dialog>
  </header>;
}
