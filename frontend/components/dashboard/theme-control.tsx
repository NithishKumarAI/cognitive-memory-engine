"use client";
import { useSyncExternalStore } from "react";
const key = "cme_theme";
function preference() { try { const value = localStorage.getItem(key); return value === "light" || value === "dark" ? value : "system"; } catch { return "system"; } }
function apply() { const value = preference(); const dark = value === "dark" || value === "system" && matchMedia("(prefers-color-scheme: dark)").matches; document.documentElement.dataset.theme = dark ? "dark" : "light"; document.documentElement.style.colorScheme = dark ? "dark" : "light"; }
function subscribe(callback: () => void) { const media = matchMedia("(prefers-color-scheme: dark)"); const update = () => { apply(); callback(); }; media.addEventListener("change", update); window.addEventListener("storage", update); window.addEventListener("theme-change", update); return () => { media.removeEventListener("change", update); window.removeEventListener("storage", update); window.removeEventListener("theme-change", update); }; }
export function ThemeControl() {
  const theme = useSyncExternalStore(subscribe, preference, () => "system");
  return <select aria-label="Appearance" className="h-11 max-w-24 rounded-xl border border-border bg-card px-2 text-xs" value={theme} onChange={event => { try { localStorage.setItem(key, event.target.value); } catch {} apply(); window.dispatchEvent(new Event("theme-change")); }}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select>;
}
