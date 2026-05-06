# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: test_e2e.spec.ts >> E2Eテスト - 備品管理・貸出管理アプリ >> E2E-005: 備品を削除できる
- Location: tests/test_e2e.spec.ts:171:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="text"]')

```

# Page snapshot

```yaml
- generic [ref=e2]: "Blocked request. This host (\"frontend\") is not allowed. To allow this host, add \"frontend\" to `server.allowedHosts` in vite.config.js."
```

# Test source

```ts
  1   | /**
  2   |  * E2Eテスト - 備品管理・貸出管理アプリ
  3   |  * 
  4   |  * 要件トレーサビリティ:
  5   |  *   要件ID: RQ-FT-LOGIN, RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, 
  6   |  *           RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST, 
  7   |  *           RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST, 
  8   |  *           RQ-FT-LOGOUT, RQ-NF-ACCESS-CONTROL
  9   |  *   設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ITEM-LIST-SCREEN-UI-ITEM-LIST-SCREEN,
  10  |  *           DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN, 
  11  |  *           DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
  12  |  *   要件概要: システム全体のE2Eテストを実行する
  13  |  *   設計概要: Playwrightを使用して全機能の動作を確認する
  14  |  */
  15  | 
  16  | import { test, expect, Page } from '@playwright/test';
  17  | 
  18  | // テストデータ
  19  | const ADMIN_USER = {
  20  |   userId: 'admin',
  21  |   password: 'admin',
  22  |   role: '管理者'
  23  | };
  24  | 
  25  | const GENERAL_USER = {
  26  |   userId: 'testuser',
  27  |   password: 'testpass',
  28  |   name: 'テストユーザー',
  29  |   role: '一般利用者'
  30  | };
  31  | 
  32  | const TEST_ITEM = {
  33  |   assetNumber: 'E2E-001',
  34  |   name: 'E2Eテスト備品'
  35  | };
  36  | 
  37  | const TEST_ITEM_2 = {
  38  |   assetNumber: 'E2E-002',
  39  |   name: 'E2Eテスト備品2'
  40  | };
  41  | 
  42  | /**
  43  |  * ログイン処理のヘルパー関数
  44  |  * 
  45  |  * 要件ID: RQ-FT-LOGIN
  46  |  * 設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
  47  |  */
  48  | async function login(page: Page, userId: string, password: string) {
  49  |   await page.goto('/login');
> 50  |   await page.fill('input[type="text"]', userId);
      |              ^ Error: page.fill: Test timeout of 30000ms exceeded.
  51  |   await page.fill('input[type="password"]', password);
  52  |   await page.click('button[type="submit"]');
  53  | }
  54  | 
  55  | /**
  56  |  * ログアウト処理のヘルパー関数
  57  |  * 
  58  |  * 要件ID: RQ-FT-LOGOUT
  59  |  * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
  60  |  */
  61  | async function logout(page: Page) {
  62  |   await page.click('button:has-text("ログアウト")');
  63  | }
  64  | 
  65  | test.describe('E2Eテスト - 備品管理・貸出管理アプリ', () => {
  66  |   
  67  |   /**
  68  |    * E2E-001: ログイン機能テスト
  69  |    * 
  70  |    * 要件ID: RQ-FT-LOGIN
  71  |    * 設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
  72  |    * 要件概要: ユーザーIDとパスワードでログインできる
  73  |    * 設計概要: 正しい認証情報でログインし、備品一覧画面に遷移することを確認する
  74  |    */
  75  |   test('E2E-001: 管理者でログインできる', async ({ page }) => {
  76  |     await login(page, ADMIN_USER.userId, ADMIN_USER.password);
  77  |     
  78  |     // ログイン成功後、備品一覧画面に遷移することを確認
  79  |     await expect(page).toHaveURL('/items');
  80  |     await expect(page.locator('text=備品一覧')).toBeVisible();
  81  |     await expect(page.locator(`text=${ADMIN_USER.userId} (${ADMIN_USER.role})`)).toBeVisible();
  82  |   });
  83  |   
  84  |   /**
  85  |    * E2E-002: 備品一覧表示テスト
  86  |    * 
  87  |    * 要件ID: RQ-FT-VIEW-ITEM-LIST
  88  |    * 設計ID: DS-IF-ITEM-LIST-SCREEN-UI-ITEM-LIST-SCREEN
  89  |    * 要件概要: 備品一覧と貸出状況を表示できる
  90  |    * 設計概要: 備品一覧画面で備品リストが表示されることを確認する
  91  |    */
  92  |   test('E2E-002: 備品一覧を表示できる', async ({ page }) => {
  93  |     await login(page, ADMIN_USER.userId, ADMIN_USER.password);
  94  |     await page.goto('/items');
  95  |     
  96  |     // 備品一覧テーブルが表示されることを確認
  97  |     await expect(page.locator('text=資産管理番号')).toBeVisible();
  98  |     await expect(page.locator('text=備品名称')).toBeVisible();
  99  |     await expect(page.locator('text=ステータス')).toBeVisible();
  100 |     await expect(page.locator('text=借り主')).toBeVisible();
  101 |   });
  102 |   
  103 |   /**
  104 |    * E2E-003: 備品登録テスト
  105 |    * 
  106 |    * 要件ID: RQ-FT-REGISTER-ITEM
  107 |    * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
  108 |    * 要件概要: 管理者が備品を新規登録できる
  109 |    * 設計概要: 備品管理画面で新規登録ダイアログを開き、備品を登録することを確認する
  110 |    */
  111 |   test('E2E-003: 備品を登録できる', async ({ page }) => {
  112 |     await login(page, ADMIN_USER.userId, ADMIN_USER.password);
  113 |     await page.goto('/items/manage');
  114 |     
  115 |     // 新規登録ボタンをクリック
  116 |     await page.click('button:has-text("新規登録")');
  117 |     
  118 |     // 備品情報を入力
  119 |     await page.fill('input[label="資産管理番号"]', TEST_ITEM.assetNumber);
  120 |     await page.fill('input[label="備品名称"]', TEST_ITEM.name);
  121 |     
  122 |     // 登録ボタンをクリック
  123 |     await page.click('button:has-text("登録")');
  124 |     
  125 |     // 登録された備品がテーブルに表示されることを確認
  126 |     await expect(page.locator(`text=${TEST_ITEM.assetNumber}`)).toBeVisible();
  127 |     await expect(page.locator(`text=${TEST_ITEM.name}`)).toBeVisible();
  128 |   });
  129 |   
  130 |   /**
  131 |    * E2E-004: 備品編集テスト
  132 |    * 
  133 |    * 要件ID: RQ-FT-EDIT-ITEM
  134 |    * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
  135 |    * 要件概要: 管理者が備品情報を編集できる
  136 |    * 設計概要: 備品管理画面で編集ダイアログを開き、備品名称を変更することを確認する
  137 |    */
  138 |   test('E2E-004: 備品を編集できる', async ({ page }) => {
  139 |     await login(page, ADMIN_USER.userId, ADMIN_USER.password);
  140 |     await page.goto('/items/manage');
  141 |     
  142 |     // 既存の備品の編集ボタンをクリック（先にテスト備品を登録）
  143 |     await page.click('button:has-text("新規登録")');
  144 |     await page.fill('input[label="資産管理番号"]', TEST_ITEM_2.assetNumber);
  145 |     await page.fill('input[label="備品名称"]', TEST_ITEM_2.name);
  146 |     await page.click('button:has-text("登録")');
  147 |     
  148 |     // 編集ボタンをクリック（TEST_ITEM_2の行の編集アイコン）
  149 |     const row = page.locator(`tr:has-text("${TEST_ITEM_2.assetNumber}")`);
  150 |     await row.locator('button[aria-label="edit"]').first().click();
```