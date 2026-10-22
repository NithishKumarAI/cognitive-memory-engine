"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { ArrowUpRight, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PriorityBadge } from "./priority-badge";
import { captureHref } from "@/lib/routes";
import { recordLearningAction } from "@/services/learning";
import { useAuth } from "@/hooks/useAuth";
import type { EvidenceRecommendation, LearningActionCreate, ActionStatus } from "@/types/continuity";
export function RecommendationCard({ recommendation: rec, onSaved }: { recommendation: EvidenceRecommendation; onSaved: () => void }) {
  const { user } = useAuth(); const busyRef = useRef(false); const [busy, setBusy] = useState(false); const [feedback, setFeedback] = useState<string | null>(null);
  const resolution = rec.type === "unresolved_difficulty" || rec.type === "open_question";
  async function record(status: ActionStatus) {
    if (!user || busyRef.current) return; busyRef.current = true; setBusy(true); setFeedback(null);
    try {
      const storageKey = `cme-feedback:${user.id}:${rec.id}:${status}`;
      const prior = sessionStorage.getItem(storageKey);
      const payload: LearningActionCreate = prior ? JSON.parse(prior) : {
        idempotency_key: crypto.randomUUID(), action_type: rec.type === "intended_next_step" ? "next_step" : rec.type === "unresolved_difficulty" ? "difficulty" : rec.type === "open_question" ? "question" : rec.type === "review_suggestion" ? "review" : "recommendation",
        status, recommendation_id: rec.id, observation_id: rec.source_observation_id ?? null, capture_id: rec.source_capture_id ?? null, learning_track_id: rec.learning_track_id ?? null, topic: rec.topic,
      };
      sessionStorage.setItem(storageKey, JSON.stringify(payload));
      await recordLearningAction(payload);
      setFeedback(status === "dismissed" ? "Recommendation dismissed." : status === "resolved" ? "Your resolution has been recorded." : "Action completion recorded.");
      onSaved();
    } catch { setFeedback("Could not record feedback. Retry this action; the same request key will be reused."); }
    finally { busyRef.current = false; setBusy(false); }
  }
  const destination = rec.source_capture_id ? captureHref(rec.source_capture_id, rec.source_observation_id) : rec.learning_track_id ? `/dashboard/learning-tracks#track-${rec.learning_track_id}` : "/dashboard/history";
  return <Card className="flex flex-col p-5 sm:p-6"><div className="flex flex-wrap items-center gap-2"><PriorityBadge priority={rec.priority} /><span className="text-xs font-medium text-muted-foreground">{rec.learning_track_name ?? rec.topic}</span></div><h3 className="mt-4 text-base font-semibold leading-relaxed">{rec.action}</h3><p className="mt-2 text-sm text-muted-foreground">{rec.reason}</p>{rec.evidence ? <blockquote className="my-4 border-l-2 border-primary/40 pl-4 text-sm text-muted-foreground">{rec.evidence}</blockquote> : null}<Link className="mt-3 inline-flex min-h-11 items-center gap-1 text-sm font-medium text-primary" href={destination}>View supporting record <ArrowUpRight className="size-4" aria-hidden="true" /></Link><div className="mt-auto flex flex-wrap gap-2 pt-5"><Button disabled={busy || !user} onClick={() => void record(resolution ? "resolved" : "completed")} variant="secondary"><Check aria-hidden="true" />{resolution ? "Mark resolved" : "Mark complete"}</Button><Button disabled={busy || !user} onClick={() => void record("dismissed")} variant="ghost"><X aria-hidden="true" />Dismiss</Button></div>{feedback ? <p role="status" className="mt-3 text-sm">{feedback}</p> : null}</Card>;
}
