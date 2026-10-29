"use client";
import { useEffect, useState } from "react";
import { getAIConfiguration, saveAIKey, removeAIKey, AIConfiguration } from "@/services/ai-configuration";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function SettingsPage() {
  const [configuration, setConfiguration] = useState<AIConfiguration | null>(null);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => { let active = true; getAIConfiguration().then(value => { if (active) { setConfiguration(value); setError(""); } }).catch(() => { if (active) setError("Unable to load AI configuration. Retry when the backend is available."); }); return () => { active = false; }; }, [refresh]);
  async function update(remove = false) {
    setBusy(true); setError(""); setNotice("");
    try { if (remove) await removeAIKey(); else await saveAIKey(key); setKey(""); setConfiguration(await getAIConfiguration()); setNotice(remove ? "Your key was removed. Manual learning capture is still available." : "Your key was saved securely. It will not be displayed again."); }
    catch { setKey(""); setError("Unable to update your key. Check the connection and whether secure storage is configured."); }
    finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-2xl space-y-6"><header><h1 className="text-3xl font-semibold">AI Configuration</h1><p className="mt-3 text-muted-foreground">{configuration?.edition === "demo" ? "This demonstration supports manual capture and saved learning evidence. Live AI, voice transcription and personal keys are unavailable." : "Use your own Gemini key for learning analysis, assistant answers and consented voice transcription. Google Gemini may charge for usage. Manual learning capture works without a key."}</p></header>
    {error ? <div role="alert"><p>{error}</p><Button variant="outline" onClick={() => setRefresh(value => value + 1)}>Retry configuration</Button></div> : null}
    {notice ? <p role="status">{notice}</p> : null}
    <Card className="space-y-4 p-6"><p role="status">{configuration ? configuration.edition === "demo" ? "Live AI and personal keys are disabled in this demo." : configuration.configured ? "A personal key is saved." : "No personal key is saved." : "Checking configuration…"}</p>
      {configuration?.edition === "product" ? <><p className="text-sm text-muted-foreground">Saved keys are encrypted on the server and used only for your account. Removing or replacing a key affects subsequent requests; an already running request may finish.</p>
      {!configuration.storage_ready ? <p role="status">The operator must configure secure key storage before you can add a key.</p> : null}
      <form className="space-y-4" onSubmit={event => { event.preventDefault(); void update(); }}><Label htmlFor="gemini-key">New Gemini API key</Label><Input id="gemini-key" type="password" autoComplete="off" maxLength={256} value={key} onChange={event => setKey(event.target.value)} disabled={busy || !configuration.storage_ready} /><Button disabled={busy || !configuration.storage_ready || key.trim().length < 20}>{configuration.configured ? "Replace key" : "Save key"}</Button></form>
      {configuration.configured ? <Button variant="outline" disabled={busy} onClick={() => void update(true)}>Remove key</Button> : null}</> : null}
    </Card></div>;
}
