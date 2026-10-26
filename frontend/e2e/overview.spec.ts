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
    for (const theme of ["light", "dark"]) {
      await page.getByLabel("Appearance").selectOption(theme);
      const images = page.getByRole("img");
      await expect(images).toHaveCount(3);
      for (const image of await images.all()) {
        await image.scrollIntoViewIfNeeded();
        await expect.poll(() => image.evaluate(node => (node as HTMLImageElement).complete && (node as HTMLImageElement).naturalWidth > 0)).toBeTruthy();
      }
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
    await page.getByRole("navigation", { name: "Public navigation" }).getByRole("link", { name: "Register", exact: true }).click();
    await expect(page).toHaveURL(/\/register$/);
    await expect(page.getByText("LearnTrack · Your AI learning continuity companion.")).toBeVisible();
  });
}
