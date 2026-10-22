"use client";
import { useEffect, useState } from "react";
import { getLearningRecommendations } from "@/services/learning";
import { RecommendationCard } from "@/components/recommendations/recommendation-card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/dashboard/page-header";
import type { EvidenceRecommendation } from "@/types/continuity";
export default function RecommendationsPage() {
 const [items, setItems] = useState<EvidenceRecommendation[]>([]); const [error, setError] = useState(false); const [loading, setLoading] = useState(true); const [refresh, setRefresh] = useState(0); const [saved, setSaved] = useState(false);
 useEffect(() => { let active = true; getLearningRecommendations(50).then(result => { if (active) { setItems(result); setError(false); } }).catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, [refresh]);
 return <div className="space-y-6"><PageHeader title="Your next actions" description="A few thoughtful next steps, drawn from what you have confirmed. No invented curriculum or mastery score." />{saved ? <p role="status" className="rounded-2xl border border-border bg-sidebar-accent p-4 text-sm">Feedback saved. Your suggestions have been updated.</p> : null}{error ? <div role="alert"><p>We could not load your next actions.</p><button className="min-h-11 underline" onClick={() => setRefresh(value => value + 1)}>Try again</button></div> : loading ? <Skeleton /> : items.length ? <><p className="text-sm text-muted-foreground">Showing {items.length} suggestions (up to 50). Completing an action or resolving a question records your feedback, not subject mastery.</p><div className="grid gap-5 md:grid-cols-2">{items.map(item => <RecommendationCard key={item.id} recommendation={item} onSaved={() => { setSaved(true); setRefresh(value => value + 1); }} />)}</div></> : <EmptyState title="Nothing waiting on you" description="Your recorded actions are up to date. Capture a new learning moment whenever you are ready." href="/dashboard/capture" />}</div>;
}
