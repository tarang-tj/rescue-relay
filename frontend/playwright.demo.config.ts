import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./demo",
  outputDir: "/tmp/rescue-relay-demo-playwright",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "line",
  timeout: 240_000,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:5175",
    browserName: "chromium",
    viewport: { width: 1600, height: 900 },
    video: { mode: "on", size: { width: 1600, height: 900 } },
  },
  webServer: [
    {
      command: "uv --directory .. run uvicorn rescue_relay.api:app --host 127.0.0.1 --port 8011",
      url: "http://127.0.0.1:8011/api/health",
      reuseExistingServer: false,
      env: { RESCUERELAY_DB: `/tmp/rescue-relay-demo-${process.pid}.db` },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5175",
      url: "http://127.0.0.1:5175",
      reuseExistingServer: false,
      env: { VITE_API_TARGET: "http://127.0.0.1:8011" },
    },
  ],
});
