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
  // Must be called when on /admin/equipment or /admin/users
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
  // Go back to equipment list
  await page.getByTestId('back-to-equipment-button').click()
  await page.waitForURL('**/admin/equipment')
}

async function createEquipment(page, equipmentId, name) {
  // Must be called when on /admin/equipment
  await page.getByTestId('add-equipment-button').click()
  await page.waitForURL('**/admin/equipment/new')
  await fillInput(page, 'equipment-id-input', equipmentId)
  await fillInput(page, 'equipment-name-input', name)
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/equipment')
}

// DS-FN-E2E-EQUIPMENT-MANAGEMENT-TS-VERIFY-EQUIPMENT-MANAGEMENT
test('備品管理：登録・編集・削除・貸出中削除不可を確認する', async ({ page }) => {
  await loginAsAdmin(page)

  // Create test user (needed for loan)
  await createUser(page, 'eq-testuser', '備品テスト利用者')

  // 備品登録
  await createEquipment(page, 'EQ-MGMT-001', '管理テスト備品A')
  await expect(page.getByTestId('equipment-row-EQ-MGMT-001')).toBeVisible()

  // 備品編集
  await page.getByTestId('edit-button-EQ-MGMT-001').click()
  await page.waitForURL('**/admin/equipment/EQ-MGMT-001/edit')
  const nameInput = page.locator('[data-testid="equipment-name-input"] input')
  await nameInput.clear()
  await nameInput.fill('管理テスト備品A（更新）')
  await page.getByTestId('submit-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('equipment-row-EQ-MGMT-001')).toContainText('管理テスト備品A（更新）')

  // 貸出中備品を作成
  await createEquipment(page, 'EQ-MGMT-002', '管理テスト備品B')

  // EQ-MGMT-002 を貸出
  await page.getByTestId('loan-button-EQ-MGMT-002').click()
  await page.waitForURL('**/admin/equipment/EQ-MGMT-002/loan')
  await selectOption(page, 'user-select', '備品テスト利用者')
  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  // EQ-MGMT-001（貸出可能）を削除できる
  await page.getByTestId('delete-button-EQ-MGMT-001').click()
  await page.waitForURL('**/admin/equipment/EQ-MGMT-001/delete')
  await page.getByTestId('confirm-delete-button').click()
  await page.waitForURL('**/admin/equipment')
  await expect(page.getByTestId('equipment-row-EQ-MGMT-001')).not.toBeVisible()

  // EQ-MGMT-002（貸出中）には削除ボタンがなく返却ボタンがある
  await expect(page.getByTestId('return-button-EQ-MGMT-002')).toBeVisible()
  await expect(page.getByTestId('delete-button-EQ-MGMT-002')).not.toBeVisible()
})

// DS-FN-E2E-LOAN-EQUIPMENT-TS-VERIFY-LOAN-EQUIPMENT
test('貸出登録：備品状態が貸出中になり貸出先と貸出日が表示される', async ({ page }) => {
  await loginAsAdmin(page)

  await createUser(page, 'loan-testuser', '貸出テスト利用者')
  await createEquipment(page, 'EQ-LOAN-001', '貸出テスト備品')

  await page.getByTestId('loan-button-EQ-LOAN-001').click()
  await page.waitForURL('**/admin/equipment/EQ-LOAN-001/loan')
  await selectOption(page, 'user-select', '貸出テスト利用者')

  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  const row = page.getByTestId('equipment-row-EQ-LOAN-001')
  await expect(row).toContainText('貸出中')
  await expect(row).toContainText(today)
})

// DS-FN-E2E-RETURN-EQUIPMENT-TS-VERIFY-RETURN-EQUIPMENT
test('返却処理：備品状態が貸出可能に戻り貸出先と貸出日が消える', async ({ page }) => {
  await loginAsAdmin(page)

  await createUser(page, 'return-testuser', '返却テスト利用者')
  await createEquipment(page, 'EQ-RETURN-001', '返却テスト備品')

  await page.getByTestId('loan-button-EQ-RETURN-001').click()
  await page.waitForURL('**/admin/equipment/EQ-RETURN-001/loan')
  await selectOption(page, 'user-select', '返却テスト利用者')
  const today = new Date().toISOString().split('T')[0]
  await page.locator('[data-testid="loan-date-input"] input').fill(today)
  await page.getByTestId('submit-loan-button').click()
  await page.waitForURL('**/admin/equipment')

  await page.getByTestId('return-button-EQ-RETURN-001').click()
  await page.waitForURL('**/admin/equipment/EQ-RETURN-001/return')
  await page.getByTestId('confirm-return-button').click()
  await page.waitForURL('**/admin/equipment')

  const row = page.getByTestId('equipment-row-EQ-RETURN-001')
  await expect(row).toContainText('貸出可能')
  await expect(row).not.toContainText(today)
})
