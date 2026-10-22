import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e", fullyParallel: false, workers: 1, timeout: 90000,
  expect: { timeout: 15000 }, reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL: "http://127.0.0.1:3100", viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce", trace: "off", screenshot: "only-on-failure" },
  webServer: [
    { command: `"${process.env.E2E_PYTHON ?? "python"}" ../backend/tests/e2e_server.py`, url: "http://127.0.0.1:8100/health", timeout: 120000, reuseExistingServer: false },
    { command: process.env.E2E_PRODUCTION === "1" ? "npm run start -- --hostname 127.0.0.1 --port 3100" : "npm run dev -- --hostname 127.0.0.1 --port 3100", url: "http://127.0.0.1:3100", timeout: 180000, reuseExistingServer: false, env: { NEXT_PUBLIC_API_URL: "http://127.0.0.1:8100", NEXT_TELEMETRY_DISABLED: "1" } },
  ],
});
