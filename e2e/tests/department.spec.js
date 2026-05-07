/**
 * 部署表示機能 E2E テスト（mock モード）。
 *
 * 要件トレーサビリティ:
 *   要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-FT-DEPT-NAME-API, RQ-FT-LOAN-EQUIPMENT, RQ-DT-EQUIPMENT-RESERVED-STATUS
 *   設計ID: DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL,
 *            DS-FN-E2E-DEPT-LOAN-TS-VERIFY-DEPT-DISPLAY-IN-LOAN,
 *            DS-FN-E2E-DEPT-EQUIPMENT-LIST-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST,
 *            DS-FN-E2E-RESERVATION-TO-LOAN-TS-VERIFY-RESERVATION-TO-LOAN
 *   要件概要: モックDBから部署名を取得して各画面に表示すること、予約済み備品を貸出できることを検証する。
 *   設計概要: MOCK_EXTERNAL_DB=true でモッククライアントを使用し、users.json・departments.json の固定データで検証する。
 *   呼び出し先: なし
 *   呼び出し元: pytest（E2E）
 */
const { test, expect } = require('@playwright/test')

const ADMIN_ID = process.env.INITIAL_ADMIN_LOGIN_ID || 'admin'
const ADMIN_PW = process.env.INITIAL_ADMIN_PASSWORD || 'changeme'

async function fillInput(page, testId, value) {
  await page.locator(`[data-testid="${testId}"] input`).fill(value)
}

async function selectOption(page, testId, optionText) {
  await page.getByTestId(testId).click()
  await expect(page.locator('.v-overlay--active')).toBeVisible({ timeout: 5000 })
  await page.locator('.v-overlay--active .v-list-item').filter({ hasText: optionText }).click()
  await expect(page.locator('.v-overlay--active')).not.toBeVisible({ timeout: 3000 })
}

async function loginAsAdmin(page) {
  await page.goto('/login')
  await fillInput(page, 'login-id', ADMIN_ID)
  await fillInput(page, 'password', ADMIN_PW)
  await page.getByTestId('login-button').click()
  await page.waitForURL('**/admin/equipment')
}

async function createUser(page, loginId, displayName) {
  if (!page.url().includes('/admin/users')) {
    await page.getByTestId('manage-users-button').click()
    await page.waitForURL('**/admin/users')
  }
  await page.getByTestId('add-user-button').click()
  await page.waitForURL('**/admin/users/new')
  await fillInput(page, 'login-id-input', loginId)
  await fillInput(page, 'display-name-input', displayName)
  await fillInput(page, 'password-input', 'testpass123')
  await selectOption(page, 'role-select', '一般利用者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')
}

async function createEquipment(page, equipmentId, name) {
  // Must be called when already on /admin/equipment (SPA navigation to preserve auth state)
  await page.getByTestId('add-equipment-button').click()
  await page.waitForURL('**/admin/equipment/new')
  await fillInput(page, 'equipment-id-input', equipmentId)
  await fillInput(page, 'equipment-name-input', name)
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/equipment')
}

// DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL
test('部署表示：利用者一覧の部署列にモックDBからの部署名が表示される', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'U001-dept', '営業部テストユーザー')
  await page.waitForURL('**/admin/users')

  // U001-dept はモックに存在しないため "不明" が表示される
  // → "取得中..." が消えて何らかの値が表示されることを確認
  const deptCell = page.getByTestId('dept-name-U001-dept')
  await expect(deptCell).not.toContainText('取得中...', { timeout: 10000 })

  // admin ユーザーは mock data で "情報システム部" に対応する (user_id="admin")
  const adminDeptCell = page.getByTestId(`dept-name-${ADMIN_ID}`)
  await expect(adminDeptCell).not.toContainText('取得中...', { timeout: 10000 })
  await expect(adminDeptCell).toContainText('情報システム部')
})

// DS-FN-E2E-DEPT-LOAN-TS-VERIFY-DEPT-DISPLAY-IN-LOAN
test('貸出フォーム：利用者選択肢に部署名形式（利用者名（部署名））が表示される', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'U002-dept', '開発部テストユーザー')
  // Navigate back to equipment list via SPA (preserves auth state)
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
  await createEquipment(page, 'EQ-DEPT-LOAN-001', '部署貸出テスト備品')

  await page.getByTestId('loan-button-EQ-DEPT-LOAN-001').click()
  await page.waitForURL('**/admin/equipment/EQ-DEPT-LOAN-001/loan')

  // ドロップダウンを開いて "（" が含まれる形式の選択肢が表示されることを確認
  await page.getByTestId('user-select').click()
  await expect(page.locator('.v-overlay--active')).toBeVisible({ timeout: 5000 })
  await expect(page.locator('.v-overlay--active')).toContainText('（')
  await page.keyboard.press('Escape')
})

// DS-FN-E2E-DEPT-EQUIPMENT-LIST-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST
test('備品一覧：貸出中備品の貸出先セルに部署情報が表示される', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'U003-dept', '人事部テストユーザー')
  // Navigate back to equipment list via SPA (preserves auth state)
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
  await createEquipment(page, 'EQ-DEPT-LIST-001', '部署備品一覧テスト備品')

  await page.getByTestId('loan-button-EQ-DEPT-LIST-001').click()
  await page.waitForURL('**/admin/equipment/EQ-DEPT-LIST-001/loan')
  await selectOption(page, 'user-select', '人事部テストユーザー')
  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  // 貸出先セルが表示されて利用者名を含む
  const loanUserCell = page.getByTestId('loan-user-EQ-DEPT-LIST-001')
  await expect(loanUserCell).toContainText('人事部テストユーザー')
  // "（" が含まれる形式（部署名付き）であることを確認
  await expect(loanUserCell).toContainText('（')
})

// DS-FN-E2E-RESERVATION-TO-LOAN-TS-VERIFY-RESERVATION-TO-LOAN
test('予約済み備品の貸出：ステータスが reserved の備品に貸出ボタンが表示され貸出できる', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'U004-dept', '経理部テストユーザー')
  // Navigate back to equipment list via SPA (preserves auth state)
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
  await createEquipment(page, 'EQ-RES-LOAN-001', '予約済み貸出テスト備品')

  // 予約登録（予約状況ボタン経由でSPA遷移）
  await page.getByTestId('reservation-button-EQ-RES-LOAN-001').click()
  await page.waitForURL('**/equipment/EQ-RES-LOAN-001/reservations')
  await page.getByTestId('add-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-LOAN-001/reservations/new')
  await fillInput(page, 'start-date-input', '2027-09-01')
  await fillInput(page, 'end-date-input', '2027-09-30')
  await page.getByTestId('submit-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-LOAN-001/reservations')

  // 備品一覧へ戻り、予約済みステータスと貸出ボタンを確認（SPA遷移で認証状態保持）
  await page.getByTestId('back-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('status-chip-EQ-RES-LOAN-001')).toContainText('予約済み')
  await expect(page.getByTestId('loan-button-EQ-RES-LOAN-001')).toBeVisible()

  // 予約済み備品を貸出
  await page.getByTestId('loan-button-EQ-RES-LOAN-001').click()
  await page.waitForURL('**/admin/equipment/EQ-RES-LOAN-001/loan')
  await selectOption(page, 'user-select', '経理部テストユーザー')
  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  await expect(page.getByTestId('status-chip-EQ-RES-LOAN-001')).toContainText('貸出中')
})
