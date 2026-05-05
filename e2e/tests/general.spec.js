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

// DS-FN-E2E-GENERAL-VIEW-TS-VERIFY-GENERAL-EQUIPMENT-VIEW
test('一般利用者閲覧専用：全備品の状態が表示され操作ボタンが表示されない', async ({ page }) => {
  await loginAsAdmin(page)

  // Create equipment for the test
  await page.getByTestId('add-equipment-button').click()
  await page.waitForURL('**/admin/equipment/new')
  await fillInput(page, 'equipment-id-input', 'GEN-VIEW-001')
  await fillInput(page, 'equipment-name-input', '一般閲覧テスト備品')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/equipment')

  // Create general user
  await page.getByTestId('manage-users-button').click()
  await page.waitForURL('**/admin/users')
  await page.getByTestId('add-user-button').click()
  await page.waitForURL('**/admin/users/new')
  await fillInput(page, 'login-id-input', 'gen-viewer')
  await fillInput(page, 'display-name-input', '閲覧利用者')
  await fillInput(page, 'password-input', 'viewpass123')
  await selectOption(page, 'role-select', '一般利用者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')

  await page.getByTestId('logout-button').click()
  await page.waitForURL('**/login')

  await fillInput(page, 'login-id', 'gen-viewer')
  await fillInput(page, 'password', 'viewpass123')
  await page.getByTestId('login-button').click()
  await page.waitForURL('**/general/equipment')

  const row = page.getByTestId('equipment-row-GEN-VIEW-001')
  await expect(row).toBeVisible()
  await expect(row).toContainText('GEN-VIEW-001')
  await expect(row).toContainText('一般閲覧テスト備品')

  await expect(page.getByTestId('add-equipment-button')).not.toBeVisible()
  await expect(page.getByTestId('loan-button-GEN-VIEW-001')).not.toBeVisible()
  await expect(page.getByTestId('delete-button-GEN-VIEW-001')).not.toBeVisible()
  await expect(page.getByTestId('manage-users-button')).not.toBeVisible()
  await expect(page.getByTestId('logout-button')).toBeVisible()
})
