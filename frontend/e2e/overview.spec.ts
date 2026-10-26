import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdirSync } from "node:fs";

for (const width of [390, 768, 1440]) {
  test(`Public LearnTrack overview at ${width}px`, async ({ page }) => {
    const apiRequests: string[] = [];
    page.on("request", request => { if (new URL(request.url()).port === "8100") apiRequests.push(request.url()); });
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page).toHaveURL("http://127.0.0.1:3100/");
    await expect(page).toHaveTitle("LearnTrack");
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", "Your AI learning continuity companion.");
    await expect(page.locator('link[rel="icon"][type="image/svg+xml"]')).toHaveAttribute("href", /icon.svg/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Remember what you learn. Pick up where you left off.");
    await expect(page.getByText("Current V1 deployment pending verification.")).toBeVisible();
    await expect(page.locator("main img")).toHaveCount(0);
    await expect(page.locator(".story-section")).toHaveCount(5);
    await expect(page.locator(".knowledge-sky")).toHaveCSS("pointer-events", "none");
    for (const theme of ["light", "dark"]) {
      await page.getByLabel("Appearance").selectOption(theme);
      for (const section of await page.locator(".story-reveal").all()) await section.scrollIntoViewIfNeeded();
      expect(await page.locator(".sky-point").first().evaluate(node => getComputedStyle(node).animationName)).toBe("none");
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      expect(result.violations).toEqual([]);
      await page.evaluate(() => scrollTo(0, 0));
      const folder = `${process.env.E2E_ARTIFACT_DIR ?? "../test-artifacts/learntrack"}/screenshots`;
      mkdirSync(folder, { recursive: true });
      await page.screenshot({ path: `${folder}/overview-${theme}-${width}.png`, fullPage: true });
    }
    expect(apiRequests).toEqual([]);
    await page.getByRole("navigation", { name: "Public navigation" }).getByRole("link", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByText("LearnTrack · Your AI learning continuity companion.")).toBeVisible();
    await page.goto("/");
    await page.getByRole("navigation", { name: "Public navigation" }).getByRole("link", { name: "Get Started", exact: true }).click();
    await expect(page).toHaveURL(/\/register$/);
    await expect(page.getByText("LearnTrack · Your AI learning continuity companion.")).toBeVisible();
  });
}


test("Landing: motion, pause, scroll reveals and backend independence", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.route("http://127.0.0.1:8100/**", route => route.abort("connectionrefused"));
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  await expect(page.locator(".sky-point")).toHaveCount(28);
  await expect(page.locator(".sky-point").first()).toHaveCSS("animation-name", "point-drift");
  await page.getByRole("button", { name: "Pause animation", exact: true }).click();
  await expect(page.locator(".sky-point").first()).toHaveCSS("animation-play-state", "paused");
  await page.getByRole("button", { name: "Resume animation", exact: true }).click();
  await expect(page.locator(".sky-point").first()).toHaveCSS("animation-play-state", "running");
  await page.getByRole("link", { name: "Explore LearnTrack", exact: true }).click();
  await expect(page).toHaveURL(/#story$/);
  await expect(page.locator("#story")).toHaveAttribute("data-revealed", "true");
  for (const section of await page.locator(".story-reveal").all()) { await section.scrollIntoViewIfNeeded(); await expect(section).toHaveAttribute("data-revealed", "true"); }
  await expect(page.locator(".landing")).toHaveAttribute("data-active", "false");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator(".sky-point").first()).toHaveCSS("animation-name", "none");
  await page.keyboard.press("Control+Home");
  await page.getByRole("link", { name: "Skip to content", exact: true }).focus();
  await expect(page.getByRole("link", { name: "Skip to content", exact: true })).toBeFocused();
  expect(errors).toEqual([]);
});
