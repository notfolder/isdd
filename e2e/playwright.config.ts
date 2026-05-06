/**
 * Playwright設定ファイル
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-NF-RESPONSE-TIME, RQ-NF-CONCURRENT-USERS
 *   設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
 *   要件概要: E2Eテストを実行してシステム全体が正しく動作することを確認する
 *   設計概要: Playwrightを使用してフロントエンドとバックエンドの統合テストを実行する
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
