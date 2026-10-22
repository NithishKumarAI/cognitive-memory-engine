"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { transcribeRecording } from "@/services/capture";

const MAX_BYTES = 4 * 1024 * 1024;

// Convert browser MediaRecorder output to validated PCM WAV locally.
async function toWav(blob: Blob): Promise<Blob> {
  const context = new AudioContext();
  try {
    const audio = await context.decodeAudioData(await blob.arrayBuffer());
    if (audio.duration <= 0 || audio.duration > 120) throw new Error("Recordings must be at most 120 seconds.");
    const offline = new OfflineAudioContext(1, Math.ceil(audio.duration * 16000), 16000);
    const source = offline.createBufferSource(); source.buffer = audio; source.connect(offline.destination); source.start();
    const rendered = await offline.startRendering(); const samples = rendered.getChannelData(0);
    const buffer = new ArrayBuffer(44 + samples.length * 2); const view = new DataView(buffer);
    const word = (offset: number, value: string) => [...value].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)));
    word(0, "RIFF"); view.setUint32(4, buffer.byteLength - 8, true); word(8, "WAVE"); word(12, "fmt ");
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, 16000, true); view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    word(36, "data"); view.setUint32(40, samples.length * 2, true);
    samples.forEach((sample, index) => view.setInt16(44 + index * 2, Math.max(-1, Math.min(1, sample)) * 32767, true));
    return new Blob([buffer], { type: "audio/wav" });
  } finally { await context.close(); }
}

export function VoiceInput({ onTranscript, disabled }: { onTranscript: (text: string) => void; disabled: boolean }) {
  const recorder = useRef<MediaRecorder | null>(null); const stream = useRef<MediaStream | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null); const cancelled = useRef(false); const generation = useRef(0); const mounted = useRef(true);
  const [recording, setRecording] = useState(false); const [audio, setAudio] = useState<Blob | null>(null);
  const url = useMemo(() => audio ? URL.createObjectURL(audio) : null, [audio]); const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  const invalidate = useCallback(() => { generation.current += 1; }, []);
  const stopTracks = () => { stream.current?.getTracks().forEach(track => track.stop()); if (timer.current) clearTimeout(timer.current); };
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; invalidate(); cancelled.current = true; if (recorder.current?.state === "recording") recorder.current.stop(); stream.current?.getTracks().forEach(track => track.stop()); if (timer.current) clearTimeout(timer.current); };
  }, [invalidate]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);

  async function start() {
    setError(null); setAudio(null); setConsent(false);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") { setError("Microphone recording is unsupported. Type your update or upload WAV/MP3."); return; }
    const run = ++generation.current; setBusy(true);
    try {
      const nextStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current || run !== generation.current) { nextStream.getTracks().forEach(track => track.stop()); return; }
      stream.current = nextStream; cancelled.current = false;
      const next = new MediaRecorder(nextStream); recorder.current = next; const chunks: Blob[] = []; let bytes = 0;
      next.ondataavailable = event => { if (run !== generation.current) return; bytes += event.data.size; if (bytes > MAX_BYTES) { cancelled.current = true; if (next.state === "recording") next.stop(); setError("Recording exceeded 4 MiB. Try a shorter update."); } else chunks.push(event.data); };
      next.onerror = () => { if (run !== generation.current) return; cancelled.current = true; stopTracks(); setRecording(false); setError("Recording failed. You can type your update."); };
      next.onstop = async () => {
        if (run !== generation.current) return;
        stopTracks(); if (!mounted.current) return; setRecording(false);
        if (cancelled.current) return;
        setBusy(true);
        try { const wav = await toWav(new Blob(chunks, { type: next.mimeType })); if (mounted.current && run === generation.current) setAudio(wav); }
        catch (failure) { if (mounted.current && run === generation.current) setError(failure instanceof Error ? failure.message : "Unable to process recording."); }
        finally { if (mounted.current && run === generation.current) setBusy(false); }
      };
      next.start(500); setBusy(false); setRecording(true); timer.current = setTimeout(() => { if (next.state === "recording") next.stop(); }, 119000);
    } catch { if (!mounted.current || run !== generation.current) return; stopTracks(); setBusy(false); setError("Microphone permission was denied or unavailable. Type your update or upload WAV/MP3."); }
  }
  function cancel() { generation.current++; cancelled.current = true; if (recorder.current?.state === "recording") recorder.current.stop(); stopTracks(); setRecording(false); setBusy(false); setAudio(null); setConsent(false); }
  async function upload(file?: File) {
    const run = ++generation.current;
    setError(null); setConsent(false); setAudio(null);
    if (!file) return;
    if (file.size === 0 || file.size > MAX_BYTES || !/\.(wav|mp3)$/i.test(file.name)) { setError("Choose a nonempty WAV or MP3 recording up to 4 MiB and 120 seconds."); return; }
    setBusy(true);
    try { const wav = await toWav(file); if (mounted.current && run === generation.current) setAudio(wav); }
    catch { if (mounted.current && run === generation.current) setError("Invalid, unsupported or overlong recording. Choose WAV or MP3 up to 120 seconds."); }
    finally { if (mounted.current && run === generation.current) setBusy(false); }
  }
  async function transcribe() {
    if (!audio || !consent) return; const run = generation.current; setBusy(true); setError(null);
    try { const transcript = await transcribeRecording(audio, consent); if (mounted.current && run === generation.current) onTranscript(transcript); }
    catch { if (mounted.current && run === generation.current) setError("Transcription failed. Retry or type your update."); }
    finally { if (mounted.current && run === generation.current) setBusy(false); }
  }
  return <section className="space-y-3 rounded-md border border-border p-4" aria-label="Voice input">
    <p className="text-sm">Optional voice input · up to 120 seconds / 4 MiB · WAV or MP3 uploads</p>
    <div className="flex flex-wrap gap-2">
      <Button type="button" variant="outline" disabled={disabled || busy || recording} onClick={start}>Start Recording</Button>
      <Button type="button" variant="outline" disabled={!recording} onClick={() => recorder.current?.stop()}>Stop Recording</Button>
      <Button type="button" variant="outline" disabled={!recording && !audio && !busy} onClick={cancel}>Cancel Recording</Button>
    </div>
    <p role="status" className="text-sm" aria-live="polite">{recording ? "Recording… microphone active. Stops automatically after two minutes." : busy ? "Processing recording…" : "Microphone inactive. Text input is always available."}</p>
    <Label htmlFor="audio-upload">Or upload a recording</Label>
    <Input id="audio-upload" type="file" accept=".wav,.mp3,audio/wav,audio/mpeg" disabled={disabled || recording || busy} onChange={event => { void upload(event.target.files?.[0]); event.target.value = ""; }} />
    {audio && url ? <audio controls src={url} aria-label="Review recording" /> : null}
    {audio ? <><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} disabled={disabled || busy} />I agree to send this audio to Google Gemini for transcription. The app does not retain raw audio; Google’s processing policies apply.</label>
      <Button type="button" disabled={disabled || busy || !consent} onClick={transcribe}>Send audio for transcription</Button></> : null}
    {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
  </section>;
}
