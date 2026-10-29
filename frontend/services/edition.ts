import api from "./api";
export const DEMO_TOKEN_KEY = "learntrack_demo_token";
type Edition = { edition: "product" | "demo"; live_ai: boolean };
let editionRequest: Promise<Edition> | null = null;
let guestRequest: Promise<void> | null = null;

export function getEdition() {
  if (!editionRequest) editionRequest = api.get<Edition>("/edition", { timeout: 5000 }).then(response => response.data).catch(error => { editionRequest = null; throw error; });
  return editionRequest;
}

export async function ensureDemoSession() {
  sessionStorage.setItem("learntrack_demo_mode", "true");
  if (sessionStorage.getItem(DEMO_TOKEN_KEY)) return;
  if (!guestRequest) guestRequest = api.post<{ access_token: string }>("/demo/session", {}, { timeout: 20000 }).then(response => { sessionStorage.setItem(DEMO_TOKEN_KEY, response.data.access_token); }).finally(() => { guestRequest = null; });
  await guestRequest;
}

export async function resetDemo() {
  const response = await api.post<{ access_token: string }>("/demo/reset", {}, { timeout: 20000 });
  sessionStorage.setItem(DEMO_TOKEN_KEY, response.data.access_token);
  for (const key of Object.keys(sessionStorage)) if (key.startsWith("cme-feedback:")) sessionStorage.removeItem(key);
  window.location.replace("/dashboard");
}
