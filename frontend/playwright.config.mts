import { defineConfig } from "@playwright/test";

const webPort = 4193;
const apiPort = 8193;

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "*.e2e.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["line"], ["html", { open: "never" }]] : "line",
  outputDir: "artifacts/playwright-results",
  use: {
    baseURL: `http://127.0.0.1:${webPort}/copilot/`,
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  webServer: [
    {
      command: `PYTHONPATH=../backend CORS_ORIGINS=http://127.0.0.1:${webPort} python -m uvicorn e2e_server:app --app-dir ../backend --host 127.0.0.1 --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/healthz`,
      reuseExistingServer: false,
      timeout: 30_000
    },
    {
      command: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:${apiPort} npm run build && PORT=${webPort} node tests/e2e/static-server.mjs`,
      url: `http://127.0.0.1:${webPort}/copilot/`,
      reuseExistingServer: false,
      timeout: 120_000
    }
  ]
});
