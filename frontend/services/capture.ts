import api from "@/services/api";
import type { Capture, Confirmation } from "@/types/capture";
export async function manualLearning(text: string, source_type: "text" | "voice", learning_track_id: number | null) {
  return (await api.post<Capture>("/capture/manual", { text, source_type, learning_track_id })).data;
}
export async function analyzeLearning(text: string, source_type: "text" | "voice", learning_track_id: number | null) {
  return (await api.post<Capture>("/capture/analyze", { text, source_type, learning_track_id })).data;
}
export async function getCapture(id: number) { return (await api.get<Capture>(`/capture/${id}`)).data; }
export async function listCaptures() { return (await api.get<Capture[]>("/capture")).data; }
export async function confirmCapture(id: number, payload: Confirmation) { return (await api.post<Capture>(`/capture/${id}/confirm`, payload)).data; }
export async function retryCapture(id: number, expected_version: number) { return (await api.post<Capture>(`/capture/${id}/analyze`, { expected_version })).data; }
export async function discardCapture(id: number, expected_version: number) { return (await api.post<Capture>(`/capture/${id}/discard`, { expected_version })).data; }
export async function transcribeRecording(audio: Blob, consent: boolean) {
  if (!consent) throw new Error("Cloud audio consent is required.");
  return (await api.post<{ transcript: string }>("/capture/transcribe", audio, {
    headers: { "Content-Type": audio.type, "X-Audio-Consent": "true" },
  })).data.transcript;
}
