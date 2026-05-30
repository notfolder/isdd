import { expect, test } from '@playwright/test';

async function login(page: import('@playwright/test').Page, id: string, password: string) {
  await page.getByLabel('ログインID').first().fill(id);
  await page.getByLabel('パスワード').first().fill(password);
  await page.getByRole('button', { name: 'ログイン' }).click();
  await expect(page.getByRole('heading', { name: '備品一覧' })).toBeVisible();
}

async function ensureAvailableAsset(page: import('@playwright/test').Page): Promise<number> {
  const loanButtons = page.locator('button', { hasText: /^貸出_\d+$/ });
  if (await loanButtons.count()) {
    const label = await loanButtons.first().innerText();
    return Number(label.split('_')[1]);
  }

  const returnButtons = page.locator('button', { hasText: /^返却_\d+$/ });
  const returnCount = await returnButtons.count();
  if (!returnCount) {
    throw new Error('貸出/返却対象の備品が見つかりません。');
  }

  const returnLabel = await returnButtons.first().innerText();
  const returnAssetId = Number(returnLabel.split('_')[1]);
  await returnButtons.first().click();
  await page.getByLabel(`返却日_${returnAssetId}(YYYY-MM-DD)`).fill('2099-12-31');
  await page.getByRole('button', { name: '返却確定' }).click();

  const refreshedLoanButtons = page.locator('button', { hasText: /^貸出_\d+$/ });
  const refreshedLabel = await refreshedLoanButtons.first().innerText();
  return Number(refreshedLabel.split('_')[1]);
}

async function ensureLoanedAsset(page: import('@playwright/test').Page): Promise<number> {
  const returnButtons = page.locator('button', { hasText: /^返却_\d+$/ });
  if (await returnButtons.count()) {
    const label = await returnButtons.first().innerText();
    return Number(label.split('_')[1]);
  }

  const loanButtons = page.locator('button', { hasText: /^貸出_\d+$/ });
  const loanCount = await loanButtons.count();
  if (!loanCount) {
    throw new Error('貸出/返却対象の備品が見つかりません。');
  }

  const loanLabel = await loanButtons.first().innerText();
  const loanAssetId = Number(loanLabel.split('_')[1]);
  await loanButtons.first().click();
  await page.getByLabel(`貸出先_${loanAssetId}`).click();
  await page.getByRole('option', { name: '総務管理者', exact: true }).click();
  await page.getByLabel(`返却予定日_${loanAssetId}(YYYY-MM-DD)`).fill('2099-12-30');
  await page.getByRole('button', { name: '貸出確定' }).click();

  const refreshedReturnButtons = page.locator('button', { hasText: /^返却_\d+$/ });
  const refreshedLabel = await refreshedReturnButtons.first().innerText();
  return Number(refreshedLabel.split('_')[1]);
}

test('RQ-TS-VERIFY-LOGIN-ROLE-CONTROL: 権限制御', async ({ page }) => {
  await page.goto('/');

  await login(page, 'admin', 'admin123');
  await expect(page.getByRole('tab', { name: 'ユーザー管理' })).toBeVisible();

  await page.getByRole('button', { name: 'ログアウト' }).click();
  await login(page, 'viewer', 'viewer123');

  await expect(page.getByRole('tab', { name: 'ユーザー管理' })).toHaveCount(0);
});

test('RQ-TS-VERIFY-LOAN-FLOW: 貸出登録', async ({ page }) => {
  await page.goto('/');
  await login(page, 'admin', 'admin123');

  const assetId = await ensureAvailableAsset(page);
  await page.getByRole('button', { name: `貸出_${assetId}` }).click();
  await page.getByRole('button', { name: '貸出確定' }).click();
  await expect(page.getByText('貸出先と返却予定日は必須です。')).toBeVisible();

  await page.getByLabel(`貸出先_${assetId}`).click();
  await page.getByRole('option', { name: '一般利用者', exact: true }).click();
  await page.getByLabel(`返却予定日_${assetId}(YYYY-MM-DD)`).fill('2099-12-30');
  await page.getByRole('button', { name: '貸出確定' }).click();
  await expect(page.getByRole('button', { name: `返却_${assetId}` })).toBeVisible();
});

test('RQ-TS-VERIFY-RETURN-FLOW: 返却登録', async ({ page }) => {
  await page.goto('/');
  await login(page, 'admin', 'admin123');

  const assetId = await ensureLoanedAsset(page);
  await page.getByRole('button', { name: `返却_${assetId}` }).click();
  const returnInput = page.getByLabel(`返却日_${assetId}(YYYY-MM-DD)`);
  await returnInput.fill('');
  await page.getByRole('button', { name: '返却確定' }).click();
  await expect(page.getByText('返却日は必須です。')).toBeVisible();

  await returnInput.fill('2099-12-31');
  await page.getByRole('button', { name: '返却確定' }).click();
  await expect(page.getByRole('button', { name: `貸出_${assetId}` })).toBeVisible();
});

test('RQ-TS-VERIFY-STATUS-VISIBILITY: 一覧可視化', async ({ page }) => {
  await page.goto('/');
  await login(page, 'viewer', 'viewer123');

  await expect(page.getByText('管理番号')).toBeVisible();
  await expect(page.getByText('状態')).toBeVisible();
  await expect(page.getByText('貸出中利用者')).toBeVisible();
  await expect(page.getByText('AST001')).toBeVisible();
  await expect(page.getByText('AST002')).toBeVisible();
});
