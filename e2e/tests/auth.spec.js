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

// DS-FN-E2E-INIT-ADMIN-TS-VERIFY-INITIAL-ADMIN-CREATION
test('初期管理者作成確認：環境変数の管理者IDとパスワードでログインできる', async ({ page }) => {
  await page.goto('/login')
  await fillInput(page, 'login-id', ADMIN_ID)
  await fillInput(page, 'password', ADMIN_PW)
  await page.getByTestId('login-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('add-equipment-button')).toBeVisible()
})

// DS-FN-E2E-ADMIN-LOGIN-TS-VERIFY-ADMIN-LOGIN
test('管理者ログイン：備品一覧画面に遷移し管理者操作ボタンが表示される', async ({ page }) => {
  await loginAsAdmin(page)
  await expect(page.getByTestId('add-equipment-button')).toBeVisible()
  await expect(page.getByTestId('manage-users-button')).toBeVisible()
  await expect(page.getByTestId('logout-button')).toBeVisible()
})

// DS-FN-E2E-GENERAL-LOGIN-TS-VERIFY-GENERAL-LOGIN
test('一般利用者ログイン：一般向け備品一覧画面に遷移し操作ボタンが表示されない', async ({ page }) => {
  await loginAsAdmin(page)
  // Navigate to user management via button click (preserves Pinia state)
  await page.getByTestId('manage-users-button').click()
  await page.waitForURL('**/admin/users')
  await page.getByTestId('add-user-button').click()
  await page.waitForURL('**/admin/users/new')
  await fillInput(page, 'login-id-input', 'auth-general')
  await fillInput(page, 'display-name-input', '一般利用者テスト')
  await fillInput(page, 'password-input', 'generalpass')
  await selectOption(page, 'role-select', '一般利用者')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/users')

  await page.getByTestId('logout-button').click()
  await page.waitForURL('**/login')

  await fillInput(page, 'login-id', 'auth-general')
  await fillInput(page, 'password', 'generalpass')
  await page.getByTestId('login-button').click()
  await page.waitForURL('**/general/equipment')

  await expect(page.getByTestId('logout-button')).toBeVisible()
  await expect(page.getByTestId('add-equipment-button')).not.toBeVisible()
})

// DS-FN-E2E-LOGOUT-TS-VERIFY-LOGOUT
test('ログアウト：ログイン画面に遷移し管理者画面へのアクセス時に再ログインが要求される', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByTestId('logout-button').click()
  await page.waitForURL('**/login')

  await page.goto('/admin/equipment')
  await page.waitForURL('**/login')
  await expect(page.getByTestId('login-button')).toBeVisible()
})

// DS-FN-E2E-AUTO-LOGOUT-TS-VERIFY-AUTO-LOGOUT
test('自動ログアウト：60分経過後にセッションが切れログイン画面に遷移する', async ({ page }) => {
  await page.clock.install()
  await loginAsAdmin(page)
  await page.waitForURL('**/admin/equipment')

  await page.clock.fastForward(61 * 60 * 1000)
  await expect(page).toHaveURL(/login/, { timeout: 15000 })
  await expect(page.getByTestId('login-button')).toBeVisible()
})
