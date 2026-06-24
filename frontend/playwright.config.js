import { defineConfig } from "@playwright/test";
import process from "node:process";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: process.env.CREST_UI_BASE_URL || "http://127.0.0.1:5173",
    channel: process.platform === "win32" ? "msedge" : undefined,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    viewport: { width: 1478, height: 1000 },
  },
});
