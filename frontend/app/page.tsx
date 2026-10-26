import Image from "next/image";
import Link from "next/link";
import { BookOpen, ArrowRight, Mic, CheckCheck, Bookmark, Compass, ChartNoAxesCombined } from "lucide-react";
import { branding } from "@/lib/branding";
import { Button } from "@/components/ui/button";
import { ThemeControl } from "@/components/dashboard/theme-control";
import home from "@/public/showcase/home.png";
import recommendations from "@/public/showcase/recommendations.png";
import analytics from "@/public/showcase/analytics.png";

const steps = [
  { icon: Mic, title: "Capture in your own words", text: "Write a learning update or record your voice. Audio is sent for transcription only after consent, and you can edit the text." },
  { icon: CheckCheck, title: "Review before remembering", text: "AI drafts topics, difficulties, questions and next steps. Correct the interpretation, then explicitly confirm what belongs in your history." },
  { icon: Bookmark, title: "Keep the evidence", text: "Save confirmed observations with their original capture. Optionally create a searchable memory for semantic retrieval." },
  { icon: Compass, title: "Return with a next step", text: "Resume a checkpoint, revisit an unresolved question and follow recommendations back to the records that support them." },
];
const shots = [
  { image: home, title: "A place to pick up again", text: "A checkpoint connects your latest learning context to an exact supporting record.", alt: "Synthetic learning dashboard with a Python decorators checkpoint and next actions" },
  { image: recommendations, title: "Direction grounded in your history", text: "Next actions come from confirmed plans and difficulties. Completion records your feedback, not subject mastery.", alt: "Synthetic next actions with supporting capture links and completion controls" },
  { image: analytics, title: "Activity with honest boundaries", text: "See logged time and confirmed reflections. Self-reported understanding and activity consistency are not assessed knowledge scores.", alt: "Synthetic insights showing recorded study time, confirmed captures and activity charts" },
];

export default function Home() {
  return <>
    <a href="#main" className="skip-link">Skip to content</a>
    <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-8">
      <Link href="/" aria-label={`${branding.name} overview`} className="flex items-center gap-3 font-semibold"><span className="rounded-xl bg-primary p-2 text-primary-foreground"><BookOpen aria-hidden="true" className="size-6" /></span>{branding.name}</Link>
      <nav aria-label="Public navigation" className="flex flex-wrap items-center gap-2"><ThemeControl /><Button asChild variant="ghost"><Link href="/login">Sign in</Link></Button><Button asChild><Link href="/register">Register</Link></Button></nav>
    </header>
    <main id="main" className="mx-auto max-w-6xl px-5 pb-16 sm:px-8">
      <section className="grid items-center gap-10 py-12 md:grid-cols-[1.2fr_1fr] md:py-20" aria-labelledby="promise">
        <div><p className="mb-5 text-sm font-semibold text-primary">{branding.description}</p><h1 id="promise" className="text-4xl font-semibold tracking-tight sm:text-5xl">{branding.promise}</h1><p className="mt-6 max-w-xl text-lg text-muted-foreground">Your learning should survive the gap between study sessions. Keep what you explored, what still feels unclear and what you meant to try next in one place.</p><div className="mt-8 flex flex-wrap gap-3"><Button asChild><Link href="/register">Create your workspace <ArrowRight aria-hidden="true" /></Link></Button><Button asChild variant="outline"><a href="#workflow">See how it works</a></Button></div></div>
        <aside className="rounded-3xl border border-border bg-accent p-7 sm:p-9"><p className="text-xs font-semibold uppercase tracking-widest text-primary">From reflection to continuity</p><h2 className="mt-4 text-2xl font-semibold">A little context makes returning easier.</h2><p className="mt-4 text-muted-foreground">A saved note becomes useful when you can find the source, remember your open question and choose a next step.</p><p className="mt-6 border-t border-border pt-5 text-sm">An AI-powered learning continuity companion, built around evidence you review.</p></aside>
      </section>
      <section id="workflow" aria-labelledby="workflow-title" className="border-t border-border py-12"><p className="text-sm font-semibold text-primary">The learning workflow</p><h2 id="workflow-title" className="mt-3 text-3xl font-semibold">Your words. Your review. Your learning history.</h2><ol className="mt-8 grid gap-4 sm:grid-cols-2">{steps.map(({ icon: Icon, title, text }, index) => <li key={title} className="rounded-2xl border border-border bg-card p-6"><div className="flex items-center justify-between text-primary"><Icon aria-hidden="true" className="size-6" /><span className="text-sm">0{index + 1}</span></div><h3 className="mt-5 text-lg font-semibold">{title}</h3><p className="mt-2 text-muted-foreground">{text}</p></li>)}</ol></section>
      <section id="screenshots" aria-labelledby="screenshots-title" className="border-t border-border py-12"><h2 id="screenshots-title" className="text-3xl font-semibold">Inside the implemented workspace</h2><p className="mt-3 max-w-3xl text-muted-foreground">Actual browser-test screenshots using synthetic learning data, captured before the LearnTrack rename. These static examples show the earlier project name; they are not an anonymous AI demo.</p><div className="mt-8 space-y-10">{shots.map(shot => <figure key={shot.title} className="overflow-hidden rounded-2xl border border-border bg-card"><figcaption className="p-6"><h3 className="text-xl font-semibold">{shot.title}</h3><p className="mt-2 text-muted-foreground">{shot.text}</p><a href={shot.image.src} className="mt-3 inline-flex min-h-11 items-center text-sm font-medium text-primary">Open full screenshot: {shot.title} <ArrowRight aria-hidden="true" className="ml-2 size-4" /></a></figcaption><Image src={shot.image} alt={shot.alt} sizes="(max-width: 1152px) 100vw, 1088px" className="h-auto w-full border-t border-border" /></figure>)}</div></section>
      <section aria-labelledby="evidence-title" className="rounded-3xl border border-border bg-accent p-7 sm:p-10"><ChartNoAxesCombined aria-hidden="true" className="size-7 text-primary" /><h2 id="evidence-title" className="mt-4 text-2xl font-semibold">Learning continuity, backed by saved evidence.</h2><p className="mt-4 max-w-3xl text-muted-foreground">Search your own history, ask an assistant grounded in saved records and inspect its cited evidence. AI can misinterpret a reflection; review matters. Logged activity and confirmed reflections describe your records, not a fabricated mastery score.</p><div className="mt-6 flex flex-wrap gap-3"><Button asChild><Link href="/register">Start a learning workspace</Link></Button><Button asChild variant="outline"><Link href="/login">Sign in to your workspace</Link></Button></div></section>
    </main>
    <footer className="border-t border-border px-5 py-8 text-center text-sm text-muted-foreground"><p>{branding.name} · {branding.description}</p><p className="mt-2">Current V1 deployment pending verification.</p><a className="mt-2 inline-flex min-h-11 items-center text-primary underline" href="https://github.com/NithishKumarAI/cognitive-memory-engine">Source and local walkthrough</a></footer>
  </>;
}
