"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import api from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/dashboard/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
type Result = { id: number; kind: string; title: string; excerpt: string; url: string };
export default function SearchPage() {
 const [query, setQuery] = useState(""); const [items, setItems] = useState<Result[]>([]); const [busy, setBusy] = useState(false); const [error, setError] = useState(false); const [searched, setSearched] = useState(false);
 async function search(value: string) { if (value.trim().length < 2) return; setBusy(true); setError(false); setSearched(true); try { const result = await api.get<Result[]>("/search", { params: { q: value.trim(), limit: 30 } }); setItems(result.data); window.history.replaceState(null, "", `/dashboard/search?q=${encodeURIComponent(value.trim())}`); } catch { setError(true); } finally { setBusy(false); } }
 useEffect(() => { const value = new URLSearchParams(window.location.search).get("q"); if (value && value.trim().length >= 2) { queueMicrotask(() => { setQuery(value); void search(value); }); } }, []);
 return <div className="mx-auto max-w-3xl space-y-6"><PageHeader title="Find your way back" description="Search your paths, study logs, memories and confirmed learning. Only your own records appear." /><form role="search" className="flex gap-2" onSubmit={event => { event.preventDefault(); void search(query); }}><Input aria-label="Search query" minLength={2} maxLength={120} required placeholder="A topic, phrase, or thought…" type="search" value={query} onChange={event => setQuery(event.target.value)} /><Button disabled={busy} type="submit"><Search aria-hidden="true" />Search</Button></form>{error ? <p role="alert">Search is unavailable. Please try again.</p> : busy ? <Skeleton label="Searching your records" /> : items.length ? <><p role="status" className="text-sm text-muted-foreground">{items.length} matching records shown, up to 30.</p><ul className="space-y-3">{items.map(item => <li key={`${item.kind}-${item.id}`}><Link className="block rounded-2xl border border-border bg-card p-5 hover:border-primary" href={item.url}><span className="text-xs font-semibold uppercase tracking-wider text-primary">{item.kind.replace("_", " ")}</span><h2 className="mt-2 font-semibold">{item.title}</h2><p className="mt-2 break-words text-sm text-muted-foreground">{item.excerpt}</p></Link></li>)}</ul></> : <EmptyState title={searched ? "No matching records" : "A thought is never far away"} description={searched ? "Try a shorter phrase or a different topic. Draft captures do not appear in search." : "Enter at least two characters to search your confirmed learning and manually saved records."} />}</div>;
}
