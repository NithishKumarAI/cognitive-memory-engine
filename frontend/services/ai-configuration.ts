import api from "./api";
export type AIConfiguration = { configured: boolean; available: boolean; storage_ready: boolean; edition: "product" | "demo" };
export async function getAIConfiguration() { return (await api.get<AIConfiguration>("/settings/ai")).data; }
export async function saveAIKey(api_key: string) { await api.put("/settings/ai", { api_key }); }
export async function removeAIKey() { await api.delete("/settings/ai"); }
