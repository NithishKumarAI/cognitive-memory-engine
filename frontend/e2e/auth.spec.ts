import { test, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdirSync } from "node:fs";
const api = "http://127.0.0.1:8100";
function synthetic() { const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`; return { username: `synthetic-${suffix}`, email: `synthetic-${suffix}@example.com`, password: "synthetic-password-only" }; }
async function fill(page: Page, user = synthetic()) {
  await page.goto("/register");
  await page.getByLabel("Username", { exact: true }).fill(user.username);
  await page.getByLabel("Email", { exact: true }).fill(user.email);
  await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByLabel("Confirm Password", { exact: true }).fill(user.password);
  return user;
}
const create = (page: Page) => page.getByRole("button", { name: "Create account", exact: true });

test("Signup: confirmation, byte limits, invalid email and keyboard visibility", async ({ page }) => {
  let posts = 0;
  page.on("request", req => { if (req.method() === "POST" && req.url().endsWith("/register")) posts++; });
  const user = await fill(page);
  await page.getByLabel("Confirm Password", { exact: true }).fill("different-password");
  await create(page).click(); await expect(page.getByText("Passwords do not match.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Show password", exact: true }).focus(); await page.keyboard.press("Enter");
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute("type", "text");
  await expect(page.getByLabel("Password", { exact: true })).toHaveValue(user.password);
  await page.getByRole("button", { name: "Hide password", exact: true }).click();
  await page.getByRole("button", { name: "Show confirm password", exact: true }).click();
  await expect(page.getByLabel("Confirm Password", { exact: true })).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Hide confirm password", exact: true }).click();
  await page.getByLabel("Confirm Password", { exact: true }).fill(""); await create(page).click();
  await expect(page.getByText("Please confirm your password.", { exact: true })).toBeVisible();
  await page.getByLabel("Password", { exact: true }).fill("😀".repeat(19)); await create(page).click();
  await expect(page.getByText("Use at most 72 UTF-8 bytes (some symbols use more than one byte).", { exact: true })).toBeVisible();
  await page.getByLabel("Email", { exact: true }).fill("invalid-email"); await create(page).click();
  await expect(page.getByText("Enter a valid email address.", { exact: true })).toBeVisible();
  expect(posts).toBe(0);
});

test("Signup: real registration, whitelist payload, automatic login and no unexpected console errors", async ({ page, request }) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  const user = await fill(page);
  const response = page.waitForResponse(res => res.url().endsWith("/register") && res.request().method() === "POST");
  await create(page).click(); const saved = await response;
  expect(saved.status()).toBe(200);
  expect(Object.keys(saved.request().postDataJSON()).sort()).toEqual(["email", "password", "username"]);
  await expect(page).toHaveURL(/\/dashboard$/);
  const retry = await request.post(`${api}/register`, { data: user }); expect(retry.status()).toBe(400);
  expect((await retry.json()).detail).toBe("Email already registered");
  expect(errors).toEqual([]);
});

test("Signup: duplicate email and username feedback", async ({ page, request }) => {
  const user = synthetic(); expect((await request.post(`${api}/register`, { data: user })).ok()).toBeTruthy();
  await fill(page, { ...user, username: `${user.username}-other` }); await create(page).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Email already registered. Try signing in.");
  await page.getByLabel("Email", { exact: true }).fill(`other-${user.email}`); await page.getByLabel("Username", { exact: true }).fill(user.username); await create(page).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Username already taken.");
});

for (const failure of ["offline", "disabled", "database", "validation"] as const) {
  test(`Signup: ${failure} feedback is safe`, async ({ page }) => {
    await page.route(`${api}/register`, route => failure === "offline" ? route.abort("connectionrefused") : route.fulfill({ status: failure === "disabled" ? 403 : failure === "database" ? 503 : 422, contentType: "application/json", body: JSON.stringify({ detail: failure === "validation" ? [{ input: "DO-NOT-RENDER", msg: "private-server-detail" }] : "private-server-detail" }) }));
    await fill(page); await create(page).click();
    const expected = { offline: "Unable to connect to the LearnTrack server. Check that the backend is running.", disabled: "Registration is temporarily disabled.", database: "The LearnTrack database or service is unavailable.", validation: "Some form values are invalid." }[failure];
    await expect(page.getByRole("main").getByRole("alert")).toContainText(expected);
    await expect(page.getByText(/DO-NOT-RENDER|private-server-detail/)).toHaveCount(0);
  });
}

test("Signup: created account survives automatic-login failure and signs in safely", async ({ page, request }) => {
  let registrations = 0; page.on("request", req => { if (req.method() === "POST" && req.url().endsWith("/register")) registrations++; });
  await page.route(`${api}/login`, route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"unavailable"}' }));
  const user = await fill(page); await create(page).click();
  await expect(page.getByRole("status")).toContainText("Your account was created, but automatic sign-in did not finish.");
  await expect(create(page)).toHaveCount(0); expect(registrations).toBe(1);
  expect((await request.post(`${api}/register`, { data: user })).status()).toBe(400);
  await page.unroute(`${api}/login`);
  await page.getByRole("link", { name: "Sign in to your new account" }).click();
  await page.getByLabel("Email", { exact: true }).fill(user.email); await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByRole("button", { name: "Show password", exact: true }).click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveValue(user.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page).toHaveURL(/\/dashboard$/);
});

test("Signup: lost response retry cannot create duplicate account", async ({ page }) => {
  let calls = 0;
  await page.route(`${api}/register`, async route => { calls++; if (calls === 1) { await route.fetch(); await route.abort("failed"); } else await route.continue(); });
  await fill(page); await create(page).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Unable to connect");
  await create(page).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Email already registered"); expect(calls).toBe(2);
});

test("Login: wrong credentials and network failures remain distinct", async ({ page }) => {
  await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill("missing-synthetic@example.com"); await page.getByLabel("Password", { exact: true }).fill("wrong-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Invalid email or password.");
  await page.route(`${api}/login`, route => route.abort("connectionrefused")); await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Unable to connect to the LearnTrack server.");
});

test("Signup: disabled while saving and accessible forms at requested widths", async ({ page }) => {
  const folder = `${process.env.E2E_ARTIFACT_DIR ?? "../test-artifacts/ui-auth"}/screenshots`; mkdirSync(folder, { recursive: true });
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const path of ["/register", "/login"]) {
      await page.goto(path); await expect(page).toHaveTitle(path === "/register" ? "Create account | LearnTrack" : "Sign in | LearnTrack"); const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze(); expect(result.violations).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      await page.screenshot({ path: `${folder}/${path.slice(1)}-${width}.png`, fullPage: true });
    }
  }
  let release!: () => void; const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route(`${api}/register`, async route => { await pending; await route.continue(); });
  await fill(page); await create(page).click(); await expect(page.getByRole("button", { name: "Creating account…" })).toBeDisabled();
  release(); await expect(page).toHaveURL(/\/dashboard$/);
});
