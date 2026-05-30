import { defineConfig } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:8501';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  use: {
    baseURL,
    headless: true,
  },
});
