"use client";
import { useEffect, useState } from "react";
import { getEdition, resetDemo } from "@/services/edition";
import { Button } from "@/components/ui/button";

export function DemoBanner() {
  const [demo, setDemo] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; getEdition().then(value => { if (active) setDemo(value.edition === "demo"); }).catch(() => {}); return () => { active = false; }; }, []);
  if (!demo) return null;
  return <aside className="mb-6 space-y-3 rounded-2xl border border-primary/30 bg-sidebar-accent p-5" aria-label="Interactive demo"><p className="font-semibold">LearnTrack Interactive Demo</p><p className="text-sm">Explore how LearnTrack remembers learning, tracks difficulties and helps you continue where you left off.</p><p className="text-xs text-muted-foreground">Synthetic records in your temporary workspace. Live AI and voice transcription are disabled. Changes expire after two hours; avoid entering personal information.</p><div className="flex flex-wrap items-center gap-4"><a className="min-h-11 text-sm underline" href="https://github.com/NithishKumarAI/cognitive-memory-engine#readme">Full product information</a><Button variant="outline" disabled={busy} onClick={async () => { setBusy(true); setError(""); try { await resetDemo(); } catch { setError("Reset unavailable. Try again later; your current session is still available."); setBusy(false); } }}>Reset Demo</Button></div>{error ? <p role="alert">{error}</p> : null}</aside>;
}
