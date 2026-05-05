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

// DS-FN-E2E-BORROWER-MANAGEMENT-TS-VERIFY-BORROWER-MANAGEMENT
test('利用者管理：登録・編集・削除・制限を確認する', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByTestId('manage-users-button').click()
  await page.waitForURL('**/admin/users')

  // 利用者登録
  await page.getByTestId('add-user-button').click()
  await page.waitForURL('**/admin/users/new')
  await fillInput(page, 'login-id-input', 'us-newuser')
  await fillInput(page, 'display-name-input', '利用者管理テスト')
  await fillInput(page, 'password-input', 'newpass123')
  await selectOption(page, 'role-select', '一般利用者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')
  await expect(page.getByTestId('user-row-us-newuser')).toBeVisible()

  // 利用者編集（権限変更）
  await page.getByTestId('edit-user-button-us-newuser').click()
  await page.waitForURL('**/admin/users/us-newuser/edit')
  await selectOption(page, 'role-select', '管理者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')
  await expect(page.getByTestId('user-row-us-newuser')).toContainText('管理者')

  // 削除可能な利用者を削除
  await page.getByTestId('delete-user-button-us-newuser').click()
  await page.waitForURL('**/admin/users/us-newuser/delete')
  await page.getByTestId('confirm-delete-button').click()
  await page.waitForURL('**/admin/users')
  await expect(page.getByTestId('user-row-us-newuser')).not.toBeVisible()

  // 自分自身（最後の管理者）の削除を試みる → エラーが表示される
  await page.getByTestId('delete-user-button-' + ADMIN_ID).click()
  await page.waitForURL(`**/admin/users/${ADMIN_ID}/delete`)
  await page.getByTestId('confirm-delete-button').click()
  await expect(page.getByTestId('error-message')).toBeVisible()

  // 貸出中の利用者の削除を試みる → エラーが表示される
  await page.getByTestId('cancel-button').click()
  await page.waitForURL('**/admin/users')
  await page.getByTestId('add-user-button').click()
  await page.waitForURL('**/admin/users/new')
  await fillInput(page, 'login-id-input', 'us-loaneduser')
  await fillInput(page, 'display-name-input', '貸出中利用者テスト')
  await fillInput(page, 'password-input', 'loanedpass')
  await selectOption(page, 'role-select', '一般利用者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')

  // Navigate to equipment to create and loan
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
  await page.getByTestId('add-equipment-button').click()
  await page.waitForURL('**/admin/equipment/new')
  await fillInput(page, 'equipment-id-input', 'US-TEST-EQ-001')
  await fillInput(page, 'equipment-name-input', '利用者テスト用備品')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/equipment')

  await page.getByTestId('loan-button-US-TEST-EQ-001').click()
  await page.waitForURL('**/admin/equipment/US-TEST-EQ-001/loan')
  await selectOption(page, 'user-select', '貸出中利用者テスト')
  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  // Navigate back to users and try to delete the loaned user
  await page.getByTestId('manage-users-button').click()
  await page.waitForURL('**/admin/users')
  await page.getByTestId('delete-user-button-us-loaneduser').click()
  await page.waitForURL('**/admin/users/us-loaneduser/delete')
  await page.getByTestId('confirm-delete-button').click()
  await expect(page.getByTestId('error-message')).toBeVisible()
})
