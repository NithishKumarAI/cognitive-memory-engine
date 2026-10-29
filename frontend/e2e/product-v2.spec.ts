import { test, expect } from "@playwright/test";

test("Home capture works without AI and optional reads recover independently", async ({ page, request }) => {
  const suffix = Math.random().toString(36).slice(2);
  const user = { username: `v2-${suffix}`, email: `v2-${suffix}@example.com`, password: "synthetic-password" };
  expect((await request.post("http://127.0.0.1:8100/register", { data: user })).ok()).toBeTruthy();
  const login = await (await request.post("http://127.0.0.1:8100/login", { data: user })).json();
  await page.addInitScript(token => localStorage.setItem("cme_access_token", token), login.access_token);
  await page.route("**/settings/ai", route => route.fulfill({ json: { configured: false, available: false, storage_ready: false, edition: "product" } }));
  await page.route("**/learning/overview?*", route => route.fulfill({ status: 503, json: { detail: "Synthetic storage outage" } }));
  await page.route("**/learning-tracks", route => route.fulfill({ status: 503, json: { detail: "Synthetic path outage" } }));
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "What did you learn today?" })).toBeVisible();
  await expect(page.getByText("Some sections could not be loaded:")).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyze Learning", exact: true })).toBeDisabled();
  await page.getByLabel("Learning update / editable transcription").fill("I studied SQL joins and need to practice.");
  await page.getByRole("button", { name: "Review manually", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("button", { name: "Add observation", exact: true }).click();
  await page.getByLabel("Topic", { exact: true }).fill("SQL joins");
  await page.getByLabel("What to save", { exact: true }).fill("I studied SQL joins and need to practice.");
  await page.getByRole("button", { name: "Confirm and save", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Saved interpretation", exact: true })).toBeVisible();
  await page.unroute("**/learning/overview?*"); await page.unroute("**/learning-tracks");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByText("Some sections could not be loaded:")).toHaveCount(0);
  await expect(page.getByText("Recorded topics", { exact: true })).toBeVisible();
  await page.goto("/dashboard/capture");
  await expect(page.getByLabel("Recent captures", { exact: true }).locator("option")).toHaveCount(2);
});

test("Capture opens a source link when optional listings fail", async ({ page, request }) => {
  const suffix = Math.random().toString(36).slice(2);
  const user = { username: `source-${suffix}`, email: `source-${suffix}@example.com`, password: "synthetic-password" };
  expect((await request.post("http://127.0.0.1:8100/register", { data: user })).ok()).toBeTruthy();
  const login = await (await request.post("http://127.0.0.1:8100/login", { data: user })).json();
  const headers = { Authorization: `Bearer ${login.access_token}` };
  const draft = await (await request.post("http://127.0.0.1:8100/capture/manual", { headers, data: { text: "Synthetic source record" } })).json();
  await page.addInitScript(token => localStorage.setItem("cme_access_token", token), login.access_token);
  await page.route("**/learning-tracks", route => route.fulfill({ status: 503, json: { detail: "Synthetic path outage" } }));
  await page.route("**/capture", route => route.fulfill({ status: 503, json: { detail: "Synthetic history outage" } }));
  await page.goto(`/dashboard/capture?capture=${draft.id}`);
  await expect(page.getByLabel("Original input (preserved)")).toHaveValue("Synthetic source record");
  await expect(page.getByText("Recent captures are unavailable.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "New capture", exact: true }).click();
  await page.getByLabel("Learning update / editable transcription").fill("A new manual reflection.");
  await page.getByRole("button", { name: "Review manually", exact: true }).click();
  await expect(page.getByLabel("Original input (preserved)")).toHaveValue("A new manual reflection.");
});
