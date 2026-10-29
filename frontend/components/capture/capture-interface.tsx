"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { AxiosError } from "axios";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { captureHref } from "@/lib/routes";
import { VoiceInput } from "@/components/capture/voice-input";
import { analyzeLearning, manualLearning, guidedExample, getCapture, listCaptures, confirmCapture, retryCapture, discardCapture } from "@/services/capture";
import { getAIConfiguration } from "@/services/ai-configuration";
import { listLearningTracks } from "@/services/learningTracks";
import type { Capture, Interpretation, ObservationType } from "@/types/capture";
import type { LearningTrack } from "@/types/learningTrack";

const empty = (): Interpretation => ({ subject: null, topics: [], observations: [], duration_minutes: null, duration_evidence: null, ambiguity: null });
const kinds: { value: ObservationType; label: string }[] = [{ value: "learned", label: "Learned" }, { value: "understood_self_report", label: "Understanding (self-report)" }, { value: "difficulty", label: "Difficulty" }, { value: "open_question", label: "Open question" }, { value: "intended_next_step", label: "Intended next step" }];
const selectClass = "w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

export function CaptureInterface({ inline = false, onConfirmed }: { inline?: boolean; onConfirmed?: () => void }) {
  const voiceSection = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("mode") === "voice" && !params.has("capture")) {
      voiceSection.current?.focus();
      voiceSection.current?.scrollIntoView({ block: "center" });
    }
  }, []);
  const [text, setText] = useState(""); const [source, setSource] = useState<"text" | "voice">("text");
  const [capture, setCapture] = useState<Capture | null>(null); const [proposal, setProposal] = useState<Interpretation>(empty);
  const [tracks, setTracks] = useState<LearningTrack[]>([]); const [recent, setRecent] = useState<Capture[]>([]);
  const [track, setTrack] = useState(""); const [memories, setMemories] = useState(false);
  const [operation, setOperation] = useState<"analyze" | "confirm" | null>(null);
  const [loadErrors, setLoadErrors] = useState<string[]>([]);
  const [reload, setReload] = useState(0);
  const [demo, setDemo] = useState(false);
  const [aiAvailable, setAiAvailable] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  const apply = useCallback((result: Capture) => {
    setCapture(result); setText(result.original_text); setSource(result.source_type);
    setTrack(result.learning_track_id === null ? "" : String(result.learning_track_id));
    setProposal(result.confirmed_interpretation ?? result.proposed_interpretation ?? empty());
    if (!inline) window.history.replaceState(null, "", captureHref(result.id) + window.location.hash);
    setRecent(previous => [result, ...previous.filter(item => item.id !== result.id)].slice(0, 20));
  }, [inline]);
  useEffect(() => {
    let active = true;
    Promise.allSettled([listLearningTracks(), listCaptures(), getAIConfiguration()]).then(([paths, history, ai]) => {
      if (!active) return;
      const failures: string[] = [];
      if (paths.status === "fulfilled") setTracks(paths.value); else failures.push("Learning paths are unavailable. You can leave this update unassigned.");
      if (history.status === "fulfilled") setRecent(history.value); else failures.push("Recent captures are unavailable. You can still write a new update.");
      setAiAvailable(ai.status === "fulfilled" && ai.value.available);
      setDemo(ai.status === "fulfilled" && ai.value.edition === "demo");
      if (ai.status === "rejected") failures.push("AI configuration could not be checked. Manual capture remains available.");
      setLoadErrors(failures);
    });
    const id = Number(new URLSearchParams(window.location.search).get("capture"));
    if (!inline && Number.isInteger(id) && id > 0) getCapture(id).then(result => { if (active) apply(result); }).catch(() => { if (active) setError("Unable to open capture. Retry from recent captures when the service is available."); });
    return () => { active = false; };
  }, [apply, inline, reload]);
  async function perform(action: () => Promise<Capture>, stage: "analyze" | "confirm" | null = null) {
    setBusy(true); setOperation(stage); setError(null);
    try { const result = await action(); apply(result); if (stage === "confirm" && result.status === "confirmed") onConfirmed?.(); }
    catch (failure) { const detail = failure instanceof AxiosError ? failure.response?.data?.detail : null; setError(typeof detail === "string" ? detail : "Unable to save. Check the fields, reload the capture, and retry. Confirmation retries cannot create duplicates."); }
    finally { setBusy(false); setOperation(null); }
  }
  useEffect(() => {
    if (!capture || !/^#observation-\d+$/.test(window.location.hash)) return;
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: "center" });
  }, [capture]);
  const editable = !!capture && (capture.status === "pending" || capture.status === "failed");
  const readOnly = busy || !editable;
  function reset() { setCapture(null); setText(""); setSource("text"); setProposal(empty()); setTrack(""); setError(null); setMemories(false); if (!inline) window.history.replaceState(null, "", "/dashboard/capture"); }
  return <div id={inline ? "learning-input" : undefined} className="mx-auto max-w-4xl space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div>{inline ? <h2 className="text-2xl font-semibold">What did you learn today?</h2> : <h1 className="text-2xl font-semibold">Capture Learning</h1>}<p className="mt-1 text-sm text-muted-foreground">Describe your learning, review the interpretation, then confirm what to save.</p></div>{!inline || capture ? <Button variant="outline" disabled={busy} onClick={reset}>New capture</Button> : null}</div>
    {!inline || capture || busy ? <ol aria-label="Capture progress" className="grid grid-cols-3 gap-2 rounded-2xl border border-border bg-card p-3 text-sm sm:grid-cols-5">{["Compose", "Analyze", "Review", "Confirm", "Saved"].map((step, index) => { const current = capture?.status === "confirmed" ? 4 : operation === "confirm" ? 3 : operation === "analyze" ? 1 : capture ? 2 : 0; return <li key={step} aria-current={index === current ? "step" : undefined} className={`rounded-xl px-3 py-2 ${index === current ? "bg-sidebar-accent font-semibold text-primary" : "text-muted-foreground"}`}><span className="mr-2 text-xs">{index + 1}.</span>{step}</li>; })}</ol> : null}
    {loadErrors.length ? <div role="alert" className="rounded-xl border border-border p-4 text-sm">{loadErrors.map(message => <p key={message}>{message}</p>)}<Button variant="outline" onClick={() => setReload(value => value + 1)}>Retry optional data</Button></div> : null}
    {demo && !capture ? <Card className="space-y-2 p-4"><p className="text-sm">Try the review workflow with a scripted SQL example. It is not a live AI result.</p><Button variant="outline" disabled={busy} onClick={() => perform(guidedExample)}>Try guided example</Button></Card> : null}
    {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
    <Card className="space-y-4 p-4 sm:p-6">
      {!inline ? <><Label htmlFor="recent-capture">Recent captures</Label><select id="recent-capture" className={selectClass} value={capture?.id ?? ""} disabled={busy} onChange={event => { if (event.target.value) void perform(() => getCapture(Number(event.target.value))); }}><option value="">Select a saved capture</option>{recent.map(item => <option key={item.id} value={item.id}>Capture #{item.id} · {item.status}</option>)}</select>
      {!recent.length ? <p className="text-sm text-muted-foreground">No captures yet. Start with a learning update below.</p> : null}</> : null}
      <Label htmlFor="learning-text">{capture ? "Original input (preserved)" : "Learning update / editable transcription"}</Label>
      <Textarea id="learning-text" rows={8} maxLength={20000} value={text} readOnly={!!capture} disabled={busy} onChange={event => setText(event.target.value)} placeholder="What did you study? What was confusing? What would you like to try next?" />
      {!capture ? <details open={!inline}><summary className="min-h-11 cursor-pointer text-sm font-medium">Speak a learning update (optional)</summary><div ref={voiceSection} tabIndex={-1} role="region" aria-label="Voice capture" className="rounded-xl focus:ring-2 focus:ring-primary focus:ring-offset-4 focus:ring-offset-card"><VoiceInput disabled={busy || demo} onTranscript={transcript => { setText(transcript); setSource("voice"); }} /></div></details> : null}
      {!capture ? <p className="text-right text-xs text-muted-foreground">{text.length.toLocaleString()} / 20,000 characters</p> : null}
      {!capture ? <><p className="text-xs text-muted-foreground">{demo ? "Live AI and voice transcription are disabled. Manual updates and the guided example still require your review before confirmation." : "Analyze Learning sends this text to Google Gemini. The proposal is a draft; no learning facts are confirmed until you approve them."}</p><Button disabled={busy || !text.trim() || !aiAvailable} onClick={() => perform(() => analyzeLearning(text, source, track ? Number(track) : null), "analyze")}>{busy ? "Analyzing…" : "Analyze Learning"}</Button><Button variant="outline" disabled={busy || !text.trim()} onClick={() => perform(() => manualLearning(text, source, track ? Number(track) : null))}>Review manually</Button>{!aiAvailable ? <p className="text-sm text-muted-foreground">{demo ? "Live AI is disabled. Save your own update manually or try the guided example." : <>AI is unavailable. Review and save manually, or <Link className="underline" href="/dashboard/settings">configure your Gemini key</Link>.</>}</p> : null}</> : null}
      {capture ? <p role="status" className="text-sm" aria-live="polite">Capture #{capture.id} · {capture.status}. {capture.message}</p> : null}
      {capture?.status === "failed" ? <p className="text-sm">This capture has not been understood by AI. Retry analysis or enter your own interpretation below.</p> : null}
      {editable && capture ? <div className="flex flex-wrap gap-2">{!demo ? <Button variant="outline" disabled={busy} onClick={() => perform(() => retryCapture(capture.id, capture.version), "analyze")}>Retry analysis (replaces draft edits)</Button> : null}<Button variant="outline" disabled={busy} onClick={() => perform(() => discardCapture(capture.id, capture.version))}>Discard draft</Button><Button variant="outline" disabled={busy} onClick={() => perform(() => getCapture(capture.id))}>Reload saved capture</Button></div> : null}
    </Card>
    <Card className="space-y-4 p-4 sm:p-6">
      <Label htmlFor="capture-track">Existing learning track (optional)</Label>
      <select id="capture-track" className={selectClass} value={track} disabled={busy || !!capture && !editable} onChange={event => setTrack(event.target.value)}><option value="">Leave unassigned</option>{tracks.map(item => <option key={item.id} value={item.id}>{item.name}{capture?.matching_track_ids.includes(item.id) ? " (possible match)" : ""}</option>)}</select>
      <p className="text-xs text-muted-foreground">A learning path organizes related topics, such as Python or SQL. It is optional; you can save your first update without one.</p>
    </Card>
    {capture ? <Card className="space-y-5 p-4 sm:p-6">
      <div><p className="text-xs font-semibold uppercase tracking-widest text-primary">{capture.status === "confirmed" ? "Confirmed by you" : "AI proposal · your review matters"}</p><h2 className="mt-2 text-xl font-semibold">{capture.status === "confirmed" ? "Saved interpretation" : "Make this reflection your own"}</h2><p className="mt-2 text-sm text-muted-foreground">Correct the subject, select an observation type and keep only what reflects your experience.</p></div>
      <fieldset disabled={readOnly} className="space-y-5">
        <div><Label htmlFor="capture-subject">Subject (optional)</Label><Input id="capture-subject" maxLength={255} value={proposal.subject ?? ""} onChange={event => setProposal({ ...proposal, subject: event.target.value || null })} /></div>
        <div><Label htmlFor="capture-topics">Topics (one per line)</Label><Textarea id="capture-topics" value={proposal.topics.join("\n")} onChange={event => setProposal({ ...proposal, topics: event.target.value.split("\n") })} /></div>
        <div><Label htmlFor="capture-duration">Confirmed study minutes (leave blank if unknown)</Label><Input id="capture-duration" type="number" min={1} step={1} value={proposal.duration_minutes ?? ""} onChange={event => setProposal({ ...proposal, duration_minutes: event.target.value ? Number(event.target.value) : null, duration_evidence: null })} /><p className="text-xs text-muted-foreground">Providing minutes creates a study log. Unknown duration creates no study session.</p></div>
        {proposal.ambiguity ? <p className="text-sm">Uncertainty: {proposal.ambiguity}</p> : null}
        <p className="text-sm">Understanding is a self-report. Nothing here marks a topic mastered.</p>
        {proposal.observations.map((item, index) => <fieldset id={capture.observations[index]?.id ? `observation-${capture.observations[index].id}` : undefined} key={index} className="scroll-mt-24 space-y-3 rounded-2xl border border-border bg-muted/30 p-5"><legend className="px-1 text-sm">Observation {index + 1}</legend>
          <Label htmlFor={`kind-${index}`}>Type</Label><select id={`kind-${index}`} className={selectClass} value={item.observation_type} onChange={event => setProposal({ ...proposal, observations: proposal.observations.map((value, i) => i === index ? { ...value, observation_type: event.target.value as ObservationType } : value) })}>{kinds.map(kind => <option key={kind.value} value={kind.value}>{kind.label}</option>)}</select>
          <Label htmlFor={`topic-${index}`}>Topic</Label><Input id={`topic-${index}`} maxLength={255} value={item.topic} onChange={event => setProposal({ ...proposal, observations: proposal.observations.map((value, i) => i === index ? { ...value, topic: event.target.value } : value) })} />
          <Label htmlFor={`content-${index}`}>What to save</Label><Textarea id={`content-${index}`} maxLength={2000} value={item.content} onChange={event => setProposal({ ...proposal, observations: proposal.observations.map((value, i) => i === index ? { ...value, content: event.target.value } : value) })} />
          {item.evidence ? <p className="text-xs text-muted-foreground">Source excerpt: {item.evidence}</p> : null}
          <Button type="button" variant="outline" onClick={() => setProposal({ ...proposal, observations: proposal.observations.filter((_, i) => i !== index) })}>Remove observation {index + 1}</Button>
        </fieldset>)}
        {!proposal.observations.length ? <p className="text-sm text-muted-foreground">No learning observations proposed. You may add your own or save just the capture.</p> : null}
        {editable ? <Button variant="outline" disabled={proposal.observations.length >= 50} onClick={() => setProposal({ ...proposal, observations: [...proposal.observations, { observation_type: "learned", topic: "", content: "", evidence: "" }] })}>Add observation</Button> : null}
        {editable && !demo ? <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={memories} onChange={event => setMemories(event.target.checked)} />Also create a searchable memory for each confirmed observation.</label> : null}
      </fieldset>
      {editable ? <Button disabled={busy || proposal.observations.some(item => !item.topic.trim() || !item.content.trim()) || proposal.duration_minutes !== null && (!Number.isInteger(proposal.duration_minutes) || proposal.duration_minutes <= 0)} onClick={() => perform(() => confirmCapture(capture.id, { expected_version: capture.version, interpretation: { ...proposal, topics: proposal.topics.map(topic => topic.trim()).filter(Boolean) }, learning_track_id: track ? Number(track) : null, create_memories: memories }), "confirm")}>{busy ? "Saving…" : "Confirm and save"}</Button> : null}
      {capture.status === "confirmed" ? <div role="status" className="space-y-2 text-sm"><Link className="mb-4 inline-flex min-h-11 items-center font-medium text-primary" href="/dashboard">Back to Home →</Link><p>Saved {capture.observations.length} confirmed observations and {capture.observations.filter(item => item.memory_id !== null).length} memories. {capture.study_log_id ? `Study log #${capture.study_log_id} created.` : "No study log created."}</p>{capture.observations.filter(item => item.memory_id !== null).map(item => <Link className="block underline" key={item.id} href={`/dashboard/memories/${item.memory_id}`}>Memory {item.memory_id}: {item.topic}</Link>)}</div> : null}
    </Card> : null}
  </div>;
}
