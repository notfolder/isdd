/**
 * 予約機能 E2E テスト（mock モード）。
 *
 * 要件トレーサビリティ:
 *   要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR,
 *            RQ-NF-RESERVATION-CONFLICT-PREVENTION, RQ-DT-EQUIPMENT-RESERVED-STATUS
 *   設計ID: DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE,
 *            DS-FN-E2E-RESERVATION-CONFLICT-TS-VERIFY-RESERVATION-CONFLICT,
 *            DS-FN-E2E-RESERVATION-NON-OVERLAP-TS-VERIFY-RESERVATION-NON-OVERLAP,
 *            DS-FN-E2E-RESERVATION-CANCEL-TS-VERIFY-RESERVATION-CANCEL,
 *            DS-FN-E2E-ADMIN-CANCEL-RESERVATION-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION
 *   要件概要: 予約CRUD・重複チェック・キャンセル・ステータス遷移を E2E で検証する。
 *   設計概要: MOCK_EXTERNAL_DB=true で動作し、管理者・一般利用者の各シナリオを検証する。
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

async function loginAsGeneral(page, loginId, password) {
  await page.goto('/login')
  await fillInput(page, 'login-id', loginId)
  await fillInput(page, 'password', password)
  await page.getByTestId('login-button').click()
  await page.waitForURL('**/general/equipment')
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
  // Go back to equipment list via SPA (preserves auth state)
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
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

async function createReservation(page, equipmentId, startDate, endDate) {
  // Navigate to reservation page via SPA (preserves auth state)
  if (!page.url().includes(`/equipment/${equipmentId}/reservations`)) {
    await page.getByTestId(`reservation-button-${equipmentId}`).click()
    await page.waitForURL(`**/equipment/${equipmentId}/reservations`)
  }
  await page.getByTestId('add-reservation-button').click()
  await page.waitForURL(`**/equipment/${equipmentId}/reservations/new`)
  await fillInput(page, 'start-date-input', startDate)
  await fillInput(page, 'end-date-input', endDate)
  await page.getByTestId('submit-reservation-button').click()
  await page.waitForURL(`**/equipment/${equipmentId}/reservations`)
}

// DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE
test('予約登録：予約が登録されてステータスが予約済みに変わる', async ({ page }) => {
  await loginAsAdmin(page)
  await createEquipment(page, 'EQ-RES-CREATE-001', '予約登録テスト備品')

  await createReservation(page, 'EQ-RES-CREATE-001', '2027-08-01', '2027-08-10')

  // 予約一覧に登録した予約が表示される
  await expect(page.getByTestId('reservation-table')).toContainText('2027-08-01')
  await expect(page.getByTestId('reservation-table')).toContainText('2027-08-10')

  // 備品一覧でステータスが「予約済み」になる（SPA遷移で認証状態保持）
  await page.getByTestId('back-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('status-chip-EQ-RES-CREATE-001')).toContainText('予約済み')
})

// DS-FN-E2E-RESERVATION-CONFLICT-TS-VERIFY-RESERVATION-CONFLICT
test('重複予約拒否：重複する期間の予約登録は 409 エラーを表示する', async ({ page }) => {
  await loginAsAdmin(page)
  await createEquipment(page, 'EQ-RES-CONFLICT-001', '重複チェックテスト備品')

  // 1件目の予約
  await createReservation(page, 'EQ-RES-CONFLICT-001', '2027-10-01', '2027-10-10')

  // 2件目（重複期間）: 既に予約ページにいるのでそのままボタンを押す
  await page.getByTestId('add-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-CONFLICT-001/reservations/new')
  await fillInput(page, 'start-date-input', '2027-10-05')
  await fillInput(page, 'end-date-input', '2027-10-15')
  await page.getByTestId('submit-reservation-button').click()

  // エラーメッセージが表示される
  await expect(page.getByTestId('error-message')).toContainText('既に予約されています', { timeout: 5000 })
})

// DS-FN-E2E-RESERVATION-NON-OVERLAP-TS-VERIFY-RESERVATION-NON-OVERLAP
test('非重複予約：重複しない期間の予約は複数登録できる', async ({ page }) => {
  await loginAsAdmin(page)
  await createEquipment(page, 'EQ-RES-NONOVER-001', '非重複テスト備品')

  // 1件目
  await createReservation(page, 'EQ-RES-NONOVER-001', '2027-11-01', '2027-11-05')
  // 2件目（境界接触: 1件目の終了日 == 2件目の開始日 → 重複なし）: 既に予約ページにいる
  await createReservation(page, 'EQ-RES-NONOVER-001', '2027-11-05', '2027-11-10')

  // 両方の予約が一覧に表示される
  await expect(page.getByTestId('reservation-table')).toContainText('2027-11-01')
  await expect(page.getByTestId('reservation-table')).toContainText('2027-11-05')
  await expect(page.getByTestId('reservation-table')).toContainText('2027-11-10')
})

// DS-FN-E2E-RESERVATION-CANCEL-TS-VERIFY-RESERVATION-CANCEL
test('予約キャンセル：予約者本人が自分の予約をキャンセルできる', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'res-cancel-user', '予約キャンセルテスト利用者')
  await createEquipment(page, 'EQ-RES-CANCEL-001', 'キャンセルテスト備品')

  // 一般利用者でログインして予約作成（SPA遷移で認証状態保持）
  await page.context().clearCookies()
  await loginAsGeneral(page, 'res-cancel-user', 'testpass123')
  // 一般備品一覧から予約状況ページへSPA遷移
  await page.getByTestId(`reservation-button-EQ-RES-CANCEL-001`).click()
  await page.waitForURL('**/equipment/EQ-RES-CANCEL-001/reservations')
  await page.getByTestId('add-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-CANCEL-001/reservations/new')
  await fillInput(page, 'start-date-input', '2027-12-01')
  await fillInput(page, 'end-date-input', '2027-12-10')
  await page.getByTestId('submit-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-CANCEL-001/reservations')

  // キャンセルボタンが自分の予約に表示される
  const rows = page.locator('[data-testid^="reservation-row-"]')
  const firstRow = rows.first()
  const reservationId = await firstRow.getAttribute('data-testid').then(
    (id) => id.replace('reservation-row-', '')
  )
  const cancelBtn = page.getByTestId(`cancel-button-${reservationId}`)
  await expect(cancelBtn).toBeVisible()

  // キャンセル実行
  await cancelBtn.click()
  await expect(page.getByTestId('reservation-table')).not.toContainText('2027-12-01', { timeout: 5000 })
})

// DS-FN-E2E-ADMIN-CANCEL-RESERVATION-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION
test('管理者による他者の予約キャンセル：管理者は任意の予約をキャンセルできる', async ({ page }) => {
  await loginAsAdmin(page)
  await createUser(page, 'res-other-user', '他者予約テスト利用者')
  await createEquipment(page, 'EQ-RES-ADMIN-CANCEL-001', '管理者キャンセルテスト備品')

  // 一般利用者が予約を登録（SPA遷移で認証状態保持）
  await page.context().clearCookies()
  await loginAsGeneral(page, 'res-other-user', 'testpass123')
  await page.getByTestId(`reservation-button-EQ-RES-ADMIN-CANCEL-001`).click()
  await page.waitForURL('**/equipment/EQ-RES-ADMIN-CANCEL-001/reservations')
  await page.getByTestId('add-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-ADMIN-CANCEL-001/reservations/new')
  await fillInput(page, 'start-date-input', '2028-01-01')
  await fillInput(page, 'end-date-input', '2028-01-10')
  await page.getByTestId('submit-reservation-button').click()
  await page.waitForURL('**/equipment/EQ-RES-ADMIN-CANCEL-001/reservations')

  // 管理者でログインし直して同じカレンダー画面を確認（SPA遷移で認証状態保持）
  await page.context().clearCookies()
  await loginAsAdmin(page)
  await page.getByTestId(`reservation-button-EQ-RES-ADMIN-CANCEL-001`).click()
  await page.waitForURL('**/equipment/EQ-RES-ADMIN-CANCEL-001/reservations')

  // 管理者には全行にキャンセルボタンが表示される
  const rows = page.locator('[data-testid^="reservation-row-"]')
  const firstRow = rows.first()
  const reservationId = await firstRow.getAttribute('data-testid').then(
    (id) => id.replace('reservation-row-', '')
  )
  const cancelBtn = page.getByTestId(`cancel-button-${reservationId}`)
  await expect(cancelBtn).toBeVisible()

  // キャンセル実行
  await cancelBtn.click()
  await expect(page.getByTestId('reservation-table')).not.toContainText('2028-01-01', { timeout: 5000 })

  // ステータスが「貸出可能」に戻る（SPA遷移で認証状態保持）
  await page.getByTestId('back-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('status-chip-EQ-RES-ADMIN-CANCEL-001')).toContainText('貸出可能')
})
