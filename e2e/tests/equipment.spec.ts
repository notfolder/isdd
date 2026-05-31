/**
 * 備品管理E2Eテストスイート。
 * 要件ID: RQ-TS-VERIFY-LOGIN / RQ-TS-VERIFY-LOGIN-FAIL / RQ-TS-VERIFY-EQUIPMENT-LIST /
 *         RQ-TS-VERIFY-CREATE-EQUIPMENT / RQ-TS-VERIFY-LENDING / RQ-TS-VERIFY-RETURN /
 *         RQ-TS-VERIFY-DELETE-LENT-EQUIPMENT / RQ-TS-VERIFY-USER-MANAGE / RQ-TS-VERIFY-GENERAL-READONLY
 * 設計ID: DS-FN-E2E-VERIFY-LOGIN-TS-VERIFY-LOGIN
 * 要件概要: 要件定義書の全テスト用利用シナリオ（9件）を網羅する。
 * 設計概要: Playwrightでブラウザ操作とAPI呼び出しを組み合わせ、各シナリオの期待結果を検証する。
 * 呼び出し先設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN, DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN
 * 呼び出し元設計ID: なし
 */

import { test, expect, type Page, type APIRequestContext } from '@playwright/test'

const ADMIN_EMAIL = 'admin@example.com'
const ADMIN_PASSWORD = process.env.INITIAL_ADMIN_PASSWORD || 'admin1234'
const BASE = process.env.BASE_URL || 'http://localhost'

// ---- ヘルパー ----

async function adminLogin(page: Page) {
  await page.goto(`${BASE}/login`)
  await page.locator('input[type="email"]').fill(ADMIN_EMAIL)
  await page.locator('input[type="password"]').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'ログイン' }).click()
  await page.waitForURL('**/equipment')
}

async function getAdminToken(request: APIRequestContext): Promise<string> {
  const res = await request.post(`${BASE}/api/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  })
  const { access_token } = await res.json()
  return access_token
}

/** 貸出中なら返却してから削除し、新規作成する */
async function cleanAndCreateEquipment(
  request: APIRequestContext,
  token: string,
  id: string,
  name: string,
) {
  await request.post(`${BASE}/api/equipment/${id}/return`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  await request.delete(`${BASE}/api/equipment/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  await request.post(`${BASE}/api/equipment`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { management_number: id, name },
  })
}

/** 一般ユーザーを取得または作成してIDを返す */
async function getOrCreateGeneralUser(
  request: APIRequestContext,
  token: string,
  email = 'e2e-general@example.com',
  name = 'E2Eテストユーザー',
): Promise<number> {
  const res = await request.get(`${BASE}/api/users`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const users: { id: number; email: string }[] = await res.json()
  const existing = users.find((u) => u.email === email)
  if (existing) return existing.id
  const createRes = await request.post(`${BASE}/api/users`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { name, email, password: 'testpass123', role: 'general' },
  })
  const user = await createRes.json()
  return user.id
}

/** API経由で備品を貸出状態にする */
async function lendViaAPI(
  request: APIRequestContext,
  token: string,
  equipmentId: string,
  userId: number,
) {
  const today = new Date().toISOString().split('T')[0]
  const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  await request.post(`${BASE}/api/equipment/${equipmentId}/lend`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { user_id: userId, lend_date: today, expected_return_date: nextMonth },
  })
}

// ---- テスト（RQ-TS-VERIFY-LOGIN）----
test('ログイン成功確認', async ({ page }) => {
  await page.goto(`${BASE}/login`)
  await page.locator('input[type="email"]').fill(ADMIN_EMAIL)
  await page.locator('input[type="password"]').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'ログイン' }).click()
  await expect(page).toHaveURL(/equipment/)
})

// ---- テスト（RQ-TS-VERIFY-LOGIN-FAIL）----
test('ログイン失敗確認', async ({ page }) => {
  await page.goto(`${BASE}/login`)
  await page.locator('input[type="email"]').fill(ADMIN_EMAIL)
  await page.locator('input[type="password"]').fill('wrongpassword')
  await page.getByRole('button', { name: 'ログイン' }).click()
  await expect(page.locator('.v-alert')).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-EQUIPMENT-LIST）----
test('備品一覧表示確認', async ({ page }) => {
  await adminLogin(page)
  await expect(page.locator('table')).toBeVisible()
  await expect(page.getByText('備品一覧')).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-CREATE-EQUIPMENT）----
test('備品登録確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  // 既存のテストデータを削除してから実施
  await cleanAndCreateEquipment(request, token, 'E2E-REG-001', 'dummy')
  await request.delete(`${BASE}/api/equipment/E2E-REG-001`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  await adminLogin(page)
  // v-btn with `to` prop renders as <a> tag, so use text selector
  await page.locator('.v-btn:has-text("備品登録")').click()
  await page.waitForURL('**/equipment/new')

  // Vuetify input.v-field__input で入力欄を特定
  const inputs = page.locator('input.v-field__input')
  await inputs.nth(0).fill('E2E-REG-001')
  await inputs.nth(1).fill('E2Eテスト備品')
  await page.getByRole('button', { name: '保存' }).click()
  await page.waitForURL('**/equipment')
  await expect(page.getByText('E2E-REG-001')).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-LENDING）----
test('貸出処理確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  await cleanAndCreateEquipment(request, token, 'E2E-LEND-001', '貸出テスト備品')
  await getOrCreateGeneralUser(request, token)

  await adminLogin(page)
  const row = page.locator('tr').filter({ hasText: 'E2E-LEND-001' })
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: '貸出' }).click()

  const dialog = page.locator('.v-dialog')
  await expect(dialog).toBeVisible()

  // v-select で貸出先を選択
  await dialog.locator('.v-select .v-field').click()
  await page.waitForSelector('.v-overlay-container .v-list-item', { state: 'visible' })
  await page.locator('.v-overlay-container .v-list-item').first().click()

  // 貸出日・返却予定日を入力
  const today = new Date().toISOString().split('T')[0]
  const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  const dateInputs = dialog.locator('input[type="date"]')
  await dateInputs.nth(0).fill(today)
  await dateInputs.nth(1).fill(nextMonth)

  await dialog.getByRole('button', { name: '実行' }).click()
  await expect(dialog).not.toBeVisible({ timeout: 10000 })
  await expect(row.getByText('貸出中')).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-RETURN）----
test('返却処理確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  await cleanAndCreateEquipment(request, token, 'E2E-RETURN-001', '返却テスト備品')
  const userId = await getOrCreateGeneralUser(request, token)
  await lendViaAPI(request, token, 'E2E-RETURN-001', userId)

  await adminLogin(page)
  const row = page.locator('tr').filter({ hasText: 'E2E-RETURN-001' })
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: '返却' }).click()

  const dialog = page.locator('.v-dialog')
  await expect(dialog.getByText('返却確認')).toBeVisible()
  await dialog.getByRole('button', { name: '返却する' }).click()
  await expect(dialog).not.toBeVisible({ timeout: 10000 })
  await expect(row.getByText('在庫中')).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-DELETE-LENT-EQUIPMENT）----
test('貸出中備品削除不可確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  await cleanAndCreateEquipment(request, token, 'E2E-DEL-001', '削除不可テスト備品')
  const userId = await getOrCreateGeneralUser(request, token)
  await lendViaAPI(request, token, 'E2E-DEL-001', userId)

  await adminLogin(page)
  const row = page.locator('tr').filter({ hasText: 'E2E-DEL-001' })
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: '削除' }).click()

  const alert = page.locator('.v-alert')
  await expect(alert).toBeVisible()
  await expect(alert).toContainText('削除できません')
})

// ---- テスト（RQ-TS-VERIFY-USER-MANAGE）----
test('ユーザー登録確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  const newEmail = 'e2e-newuser@example.com'
  // 既存ユーザーを削除
  const listRes = await request.get(`${BASE}/api/users`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const users: { id: number; email: string }[] = await listRes.json()
  const existing = users.find((u) => u.email === newEmail)
  if (existing) {
    await request.delete(`${BASE}/api/users/${existing.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  }

  await adminLogin(page)
  // v-btn with `to` prop renders as <a> tag, so use CSS selector
  await page.locator('.v-btn:has-text("ユーザー管理")').click()
  await page.waitForURL('**/users')
  await page.locator('.v-btn:has-text("新規追加")').click()
  await page.waitForURL('**/users/new')

  // 氏名・メール・パスワード を入力（v-select の権限はデフォルト=一般のまま）
  await page.locator('input.v-field__input').nth(0).fill('E2E新規ユーザー')
  await page.locator('input[type="email"]').fill(newEmail)
  await page.locator('input[type="password"]').fill('testpass999')
  await page.getByRole('button', { name: '保存' }).click()
  await page.waitForURL('**/users')
  await expect(page.getByText(newEmail)).toBeVisible()
})

// ---- テスト（RQ-TS-VERIFY-GENERAL-READONLY）----
test('一般社員の権限確認', async ({ page, request }) => {
  const token = await getAdminToken(request)
  const generalEmail = 'e2e-readonly@example.com'
  await getOrCreateGeneralUser(request, token, generalEmail, 'E2E閲覧ユーザー')

  // 一般ユーザーでログイン
  await page.goto(`${BASE}/login`)
  await page.locator('input[type="email"]').fill(generalEmail)
  await page.locator('input[type="password"]').fill('testpass123')
  await page.getByRole('button', { name: 'ログイン' }).click()
  await page.waitForURL('**/equipment')

  // 管理者専用ページへ直接アクセス → Vue Routerガードでリダイレクト
  await page.goto(`${BASE}/users`)
  await expect(page).toHaveURL(/equipment/)
})
