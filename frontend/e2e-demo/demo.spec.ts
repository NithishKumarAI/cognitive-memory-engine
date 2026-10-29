import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdirSync } from "node:fs";

test("Anonymous visitors get isolated learning, can review an example and reset", async ({ page, browser }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText("LearnTrack Interactive Demo", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Log out", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Sign in", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "What did you learn today?", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Python Foundations", exact: true })).toBeVisible();
  const first = await page.evaluate(() => sessionStorage.getItem("learntrack_demo_token"));
  const other = await browser.newContext(); const second = await other.newPage();
  await second.goto("/"); await expect(second.getByText("LearnTrack Interactive Demo", { exact: true })).toBeVisible();
  const secondToken = await second.evaluate(() => sessionStorage.getItem("learntrack_demo_token"));
  expect(first).not.toBe(secondToken);
  await page.getByRole("button", { name: "Try guided example", exact: true }).click();
  await expect(page.getByText("not a live Gemini result", { exact: false })).toBeVisible();
  await page.getByLabel("What to save", { exact: true }).first().fill("My corrected demo reflection");
  await page.getByRole("button", { name: "Confirm and save", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Saved interpretation", exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("button", { name: "Reset Demo", exact: true }).click();
  await expect(page.getByRole("button", { name: "Try guided example", exact: true })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("learntrack_demo_token"))).not.toBe(first);
  for (const route of ["/login", "/register"]) {
    await page.goto(route); await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole("button", { name: "Try guided example", exact: true })).toBeVisible();
  }
  await second.reload(); await expect(second.getByText("LearnTrack Interactive Demo", { exact: true })).toBeVisible();
  expect(await second.evaluate(() => sessionStorage.getItem("learntrack_demo_token"))).toBe(secondToken);
  await page.goto("/dashboard/chat");
  await page.getByLabel("Ask your learning assistant").fill("Where did I stop?");
  await page.getByRole("button", { name: "Send question", exact: true }).click();
  await expect(page.getByRole("link", { name: /\[Observation/ }).first()).toBeVisible();
  expect(errors).toEqual([]);
  await other.close();
});

test("Demo layouts, themes, keyboard and evidence navigation", async ({ page }) => {
  mkdirSync("../test-artifacts/demo-v2/screenshots", { recursive: true });
  await page.goto("/");
  await expect(page.getByText("LearnTrack Interactive Demo", { exact: true })).toBeVisible();
  for (const theme of ["light", "dark"]) {
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const route of ["", "/capture", "/learning-tracks", "/history", "/recommendations", "/analytics", "/memories", "/chat", "/settings"]) {
        await page.goto(`/dashboard${route}`);
        await page.getByRole("combobox", { name: "Appearance", exact: true }).selectOption(theme);
        await expect(page.getByRole("main")).toBeVisible();
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
        const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        expect(scan.violations.map(item => item.id), `${route} ${theme} ${width}`).toEqual([]);
        if (!route || width === 1440) await page.screenshot({ path: `../test-artifacts/demo-v2/screenshots/${route.slice(1) || "home"}-${theme}-${width}.png`, fullPage: true });
      }
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 }); await page.goto("/dashboard/recommendations");
  await page.getByRole("link", { name: "View supporting record", exact: true }).first().click();
  await expect(page).toHaveURL(/capture\?capture=\d+#observation-\d+/);
  await expect(page.getByRole("heading", { name: "Saved interpretation", exact: true })).toBeVisible();
  await page.keyboard.press("Tab");
});
