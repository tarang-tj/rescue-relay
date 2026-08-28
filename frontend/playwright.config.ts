import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "/tmp/rescue-relay-playwright",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:5174",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], browserName: "chromium" } },
    { name: "mobile-chromium", use: { ...devices["iPhone 13"], browserName: "chromium" } },
  ],
  webServer: [
    {
      command: "uv --directory .. run uvicorn rescue_relay.api:app --host 127.0.0.1 --port 8010",
      url: "http://127.0.0.1:8010/api/health",
      reuseExistingServer: false,
      env: { RESCUERELAY_DB: `/tmp/rescue-relay-e2e-${process.pid}.db` },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5174",
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      env: { VITE_API_TARGET: "http://127.0.0.1:8010" },
    },
  ],
});
