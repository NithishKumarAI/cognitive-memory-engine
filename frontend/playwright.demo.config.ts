import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-demo", workers: 1, timeout: 90000,
  expect: { timeout: 15000 }, reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:3100", viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" },
  webServer: [
    { command: `"${process.env.E2E_PYTHON ?? "python"}" ../backend/tests/demo_e2e_server.py`, url: "http://127.0.0.1:8100/health", timeout: 120000, reuseExistingServer: false },
    { command: "npm run start", url: "http://127.0.0.1:3100", timeout: 120000, reuseExistingServer: false,
      env: { PORT: "3100", APP_EDITION: "demo", NEXT_TELEMETRY_DISABLED: "1" } },
  ],
});
