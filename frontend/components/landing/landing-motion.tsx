"use client";

import { useEffect, useRef, useState } from "react";
import { Pause, Play } from "lucide-react";

// CSS does the drawing. Observers only reveal once and suspend off-screen motion.
export function LandingMotion({ children }: { children: React.ReactNode }) {
  const root = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const element = root.current;
    if (!element) return;
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const sections = element.querySelectorAll<HTMLElement>(".story-reveal");
    let reveals: IntersectionObserver | undefined;
    let heroVisible = true;
    const syncVisibility = () => { element.dataset.active = String(!document.hidden && heroVisible); };
    const setup = () => {
      reveals?.disconnect();
      if (media.matches || !("IntersectionObserver" in window)) {
        element.dataset.enhanced = "false";
        return;
      }
      reveals = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) { (entry.target as HTMLElement).dataset.revealed = "true"; reveals?.unobserve(entry.target); } });
      }, { threshold: 0.08 });
      sections.forEach(section => reveals?.observe(section));
      element.dataset.enhanced = "true";
    };
    setup();
    const hero = element.querySelector(".landing-hero");
    const visibility = "IntersectionObserver" in window ? new IntersectionObserver(entries => { heroVisible = entries[0].isIntersecting; syncVisibility(); }) : undefined;
    if (hero) visibility?.observe(hero);
    document.addEventListener("visibilitychange", syncVisibility);
    media.addEventListener("change", setup);
    return () => { reveals?.disconnect(); visibility?.disconnect(); document.removeEventListener("visibilitychange", syncVisibility); media.removeEventListener("change", setup); };
  }, []);
  return <div ref={root} className="landing" data-motion={paused ? "paused" : "playing"}>
    {children}
    <button type="button" className="motion-control" aria-pressed={paused} onClick={() => setPaused(value => !value)}>
      {paused ? <Play aria-hidden="true" className="size-3" /> : <Pause aria-hidden="true" className="size-3" />}{paused ? "Resume animation" : "Pause animation"}
    </button>
  </div>;
}
