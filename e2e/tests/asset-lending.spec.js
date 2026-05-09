/**
 * E2Eテストシナリオ群。
 * 要件ID: RQ-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN
 * 設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
 * 要件概要: 管理者操作・一般ユーザー閲覧・PW変更/再設定・権限拒否・削除禁止を検証する。
 * 設計概要: Playwrightで全テストシナリオを1画面操作単位で実行し、期待結果を確認する。
 * 呼び出し先設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-VERIFY-GENERAL-USER-VIEW-BORROWER-TS-VERIFY-GENERAL-USER-VIEW-BORROWER, DS-MD-VERIFY-PASSWORD-CHANGE-AND-RESET-TS-VERIFY-PASSWORD-CHANGE-AND-RESET, DS-MD-REJECT-PRIVILEGE-VIOLATION-TS-REJECT-PRIVILEGE-VIOLATION, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
 * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 */

import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

const runId = randomUUID().slice(0, 8);

async function login(page, loginId, password) {
  /**
   * ログイン操作を実行する。
   * 要件ID: RQ-FT-AUTHENTICATE-USER
   * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 要件概要: 正しい認証情報でログイン可能であること。
   * 設計概要: ログイン画面でID/PWを入力して認証を実行する。
   * 呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-VERIFY-GENERAL-USER-VIEW-BORROWER-TS-VERIFY-GENERAL-USER-VIEW-BORROWER, DS-MD-VERIFY-PASSWORD-CHANGE-AND-RESET-TS-VERIFY-PASSWORD-CHANGE-AND-RESET, DS-MD-REJECT-PRIVILEGE-VIOLATION-TS-REJECT-PRIVILEGE-VIOLATION, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   */

  await page.goto("/");
  await page.getByLabel("ログインID", { exact: true }).fill(loginId);
  await page.getByLabel("パスワード", { exact: true }).fill(password);
  await page.getByRole("button", { name: "ログイン" }).click();
}

async function gotoAssetCreate(page) {
  /**
   * 備品登録画面へ移動する。
   * 要件ID: RQ-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 要件概要: 備品一覧から登録画面へ遷移できること。
   * 設計概要: ナビボタン押下で登録画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN
   */

  await page.getByRole("button", { name: "備品登録画面へ" }).click();
  await expect(page.getByText("備品登録")).toBeVisible();
}

async function createAsset(page, assetNumber, assetName) {
  /**
   * 備品登録フォームを送信する。
   * 要件ID: RQ-FT-REGISTER-ASSET
   * 設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 要件概要: 資産管理番号と備品名を登録できること。
   * 設計概要: 登録フォーム入力後に登録APIが成功し一覧へ反映される。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   */

  await page.getByLabel("資産管理番号").fill(assetNumber);
  await page.getByLabel("備品名").fill(assetName);
  await page.getByRole("button", { name: "登録" }).click();
  await expect(page).toHaveURL(/\/assets$/);
}

async function gotoUserCreate(page) {
  /**
   * ユーザー登録画面へ移動する。
   * 要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: ユーザー一覧から登録画面へ遷移できること。
   * 設計概要: ユーザー一覧ナビから登録画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-VERIFY-PASSWORD-CHANGE-AND-RESET-TS-VERIFY-PASSWORD-CHANGE-AND-RESET, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   */

  await page.getByRole("button", { name: "ユーザー一覧へ" }).click();
  await page.getByRole("button", { name: "ユーザー登録画面へ" }).click();
  await expect(page.getByText("ユーザー登録")).toBeVisible();
}

async function createUser(page, loginId, displayName, role, initialPassword) {
  /**
   * ユーザー登録フォームを送信する。
   * 要件ID: RQ-FT-REGISTER-USER
   * 設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 要件概要: 管理者がユーザーを手動登録できること。
   * 設計概要: 登録フォーム入力後に登録APIを実行し一覧へ反映する。
   * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-VERIFY-PASSWORD-CHANGE-AND-RESET-TS-VERIFY-PASSWORD-CHANGE-AND-RESET, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   */

  await page.getByLabel("ログインID").fill(loginId);
  await page.getByLabel("表示名").fill(displayName);
  if (role !== "一般ユーザー") {
    await page.getByRole("combobox", { name: "権限" }).click({ force: true });
    await page.getByRole("option", { name: role, exact: true }).click();
  }
  await page.getByLabel("初期PW").fill(initialPassword);
  await page.getByRole("button", { name: "登録" }).click();
  await expect(page).toHaveURL(/\/users$/);
}

async function registerLoanFromRow(page, assetNumber, borrowerDisplay, loanDate) {
  /**
   * 備品一覧行から貸出登録を実行する。
   * 要件ID: RQ-FT-REGISTER-LOAN
   * 設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 要件概要: 行末ボタンで貸出登録できること。
   * 設計概要: 対象行の貸出登録ボタンからダイアログを開き、借用者と貸出日を登録する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN, DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   */

  const toAssetListButton = page.getByRole("button", { name: "備品一覧へ" });
  if ((await toAssetListButton.count()) > 0) {
    await toAssetListButton.click();
  }
  const row = page.locator("tr", { hasText: assetNumber });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "貸出登録" }).click();
  const loanDialog = page.getByRole("dialog");
  await expect(loanDialog).toBeVisible();
  const borrowerCombobox = loanDialog.getByRole("combobox", { name: "借用者", exact: true });
  await borrowerCombobox.focus();
  await borrowerCombobox.press("ArrowDown");
  await page.getByRole("option", { name: borrowerDisplay }).click();
  await loanDialog.getByLabel("貸出日 (YYYY-MM-DD)").fill(loanDate);
  await loanDialog.getByRole("button", { name: "登録" }).click();
  await expect(row).toContainText("貸出中");
}

async function registerReturnFromRow(page, assetNumber) {
  /**
   * 備品一覧行から返却登録を実行する。
   * 要件ID: RQ-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 設計ID: DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 要件概要: 行末ボタンで返却登録し、借用者情報をクリアすること。
   * 設計概要: 対象行の返却登録ボタン押下で返却APIを実行する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 呼び出し元設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN
   */

  const row = page.locator("tr", { hasText: assetNumber });
  await row.getByRole("button", { name: "返却登録" }).click();
  await expect(row).toContainText("貸出可能");
}

test("管理者の備品登録・貸出・返却が成立する", async ({ page }) => {
  /**
   * 管理者の正常系シナリオを検証する。
   * 要件ID: RQ-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN
   * 設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 要件概要: 備品登録・貸出登録・返却登録が正しく動作すること。
   * 設計概要: 管理者操作を連続実行し、状態遷移を確認する。
   * 呼び出し先設計ID: DS-MD-VERIFY-ADMIN-REGISTER-LOAN-RETURN-TS-VERIFY-ADMIN-REGISTER-LOAN-RETURN
   * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
   */

  const assetNumber = `A-100-${runId}`;
  const borrowerLoginId = `borrower1-${runId}`;
  const borrowerDisplayName = `借用者1-${runId}`;
  const borrowerPassword = `borrower1-${runId}`;

  await login(page, "admin", "admin");
  await gotoAssetCreate(page);
  await createAsset(page, assetNumber, "テストノートPC");
  await gotoUserCreate(page);
  await createUser(page, borrowerLoginId, borrowerDisplayName, "一般ユーザー", borrowerPassword);
  await registerLoanFromRow(
    page,
    assetNumber,
    `${borrowerDisplayName} (${borrowerLoginId})`,
    "2026-05-10"
  );
  await registerReturnFromRow(page, assetNumber);
});

test("一般ユーザーが借用者表示を確認できる", async ({ page }) => {
  /**
   * 一般ユーザー閲覧シナリオを検証する。
   * 要件ID: RQ-TS-VERIFY-GENERAL-USER-VIEW-BORROWER
   * 設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 要件概要: 一般ユーザーが借用者表示を確認できること。
   * 設計概要: 貸出中レコードを作成後に一般ユーザーで閲覧し借用者名を確認する。
   * 呼び出し先設計ID: DS-MD-VERIFY-GENERAL-USER-VIEW-BORROWER-TS-VERIFY-GENERAL-USER-VIEW-BORROWER
   * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
   */

  const assetNumber = `A-101-${runId}`;
  const viewerLoginId = `viewer1-${runId}`;
  const viewerDisplayName = `一般ユーザー表示-${runId}`;
  const viewerPassword = `viewer1-${runId}`;

  await login(page, "admin", "admin");
  await gotoUserCreate(page);
  await createUser(page, viewerLoginId, viewerDisplayName, "一般ユーザー", viewerPassword);
  await page.getByRole("button", { name: "備品一覧へ" }).click();
  await gotoAssetCreate(page);
  await createAsset(page, assetNumber, "テストタブレット");
  await registerLoanFromRow(
    page,
    assetNumber,
    `${viewerDisplayName} (${viewerLoginId})`,
    "2026-05-11"
  );

  await page.getByRole("button", { name: "ログアウト" }).click();
  await login(page, viewerLoginId, viewerPassword);
  await expect(page.locator("tr", { hasText: assetNumber })).toContainText(viewerDisplayName);
});

test("自己PW変更と管理者初期PW再設定が成立する", async ({ page }) => {
  /**
   * パスワード運用シナリオを検証する。
   * 要件ID: RQ-TS-VERIFY-PASSWORD-CHANGE-AND-RESET
   * 設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
   * 要件概要: 自己PW変更と管理者再設定が利用できること。
   * 設計概要: 一般ユーザー自己変更後、管理者再設定を行い再ログインを確認する。
   * 呼び出し先設計ID: DS-MD-VERIFY-PASSWORD-CHANGE-AND-RESET-TS-VERIFY-PASSWORD-CHANGE-AND-RESET
   * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
   */

  const targetLoginId = `pwuser-${runId}`;
  const targetDisplayName = `PW変更対象-${runId}`;
  const initialPassword = `pwinit-${runId}`;
  const changedPassword = `pwnew-${runId}`;
  const resetPassword = `pwreset-${runId}`;

  await login(page, "admin", "admin");
  await gotoUserCreate(page);
  await createUser(page, targetLoginId, targetDisplayName, "一般ユーザー", initialPassword);
  await page.getByRole("button", { name: "ログアウト" }).click();

  await login(page, targetLoginId, initialPassword);
  await page.getByRole("button", { name: "パスワード変更へ" }).click();
  await page.getByLabel("現在のPW", { exact: true }).fill(initialPassword);
  await page.getByLabel("新しいPW", { exact: true }).fill(changedPassword);
  await page.getByLabel("新しいPW確認", { exact: true }).fill(changedPassword);
  await page.getByRole("button", { name: "変更" }).click();
  await page.getByRole("button", { name: "ログアウト" }).click();

  await login(page, targetLoginId, changedPassword);
  await page.getByRole("button", { name: "ログアウト" }).click();

  await login(page, "admin", "admin");
  await page.getByRole("button", { name: "ユーザー一覧へ" }).click();
  await page.getByRole("button", { name: "初期PW再設定" }).click();
  const resetDialog = page.getByRole("dialog");
  await expect(resetDialog).toBeVisible();
  const resetTargetCombobox = resetDialog.getByRole("combobox", { name: "対象ユーザー", exact: true });
  await resetTargetCombobox.focus();
  await resetTargetCombobox.press("ArrowDown");
  await page.getByRole("option", { name: targetDisplayName }).click();
  await resetDialog.getByLabel("初期PW", { exact: true }).fill(resetPassword);
  await resetDialog.getByRole("button", { name: "再設定" }).click();
  await page.getByRole("button", { name: "ログアウト" }).click();

  await login(page, targetLoginId, resetPassword);
  await expect(page).toHaveURL(/\/assets$/);
});

test("一般ユーザーの更新系操作が拒否される", async ({ page }) => {
  /**
   * 権限違反拒否シナリオを検証する。
   * 要件ID: RQ-TS-REJECT-PRIVILEGE-VIOLATION
   * 設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 要件概要: 一般ユーザーは更新系操作が拒否されること。
   * 設計概要: 一般ユーザーでは更新系ボタンが表示されず、操作できないことを確認する。
   * 呼び出し先設計ID: DS-MD-REJECT-PRIVILEGE-VIOLATION-TS-REJECT-PRIVILEGE-VIOLATION
   * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
   */

  const assetNumber = `A-103-${runId}`;
  const generalLoginId = `denyuser-${runId}`;
  const generalDisplayName = `権限拒否ユーザー-${runId}`;
  const generalPassword = `denyuser-${runId}`;

  await login(page, "admin", "admin");
  await gotoAssetCreate(page);
  await createAsset(page, assetNumber, "権限拒否テスト機");
  await gotoUserCreate(page);
  await createUser(page, generalLoginId, generalDisplayName, "一般ユーザー", generalPassword);
  await page.getByRole("button", { name: "ログアウト" }).click();

  await login(page, generalLoginId, generalPassword);
  const row = page.locator("tr", { hasText: assetNumber });
  await expect(page.getByRole("columnheader", { name: "操作" })).toHaveCount(0);
  await expect(row.getByRole("button", { name: "編集" })).toHaveCount(0);
  await expect(row.getByRole("button", { name: "削除" })).toHaveCount(0);
  await expect(row.getByRole("button", { name: "貸出登録" })).toHaveCount(0);
  await expect(row.getByRole("button", { name: "返却登録" })).toHaveCount(0);
});

test("貸出中データの削除が拒否される", async ({ page }) => {
  /**
   * 削除禁止シナリオを検証する。
   * 要件ID: RQ-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   * 設計ID: DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK
   * 要件概要: 貸出中備品と貸出保有ユーザーの削除が拒否されること。
   * 設計概要: 貸出中状態を作って備品削除・ユーザー削除を試行し拒否応答を確認する。
   * 呼び出し先設計ID: DS-MD-REJECT-DELETE-WHEN-LOAN-EXISTS-TS-REJECT-DELETE-WHEN-LOAN-EXISTS
   * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
   */

  const assetNumber = `A-102-${runId}`;
  const borrowerLoginId = `loanuser-${runId}`;
  const borrowerDisplayName = `削除拒否借用者-${runId}`;
  const borrowerPassword = `loanuser-${runId}`;

  await login(page, "admin", "admin");
  await gotoUserCreate(page);
  await createUser(page, borrowerLoginId, borrowerDisplayName, "一般ユーザー", borrowerPassword);
  await page.getByRole("button", { name: "備品一覧へ" }).click();
  await gotoAssetCreate(page);
  await createAsset(page, assetNumber, "削除拒否テスト機");
  await registerLoanFromRow(
    page,
    assetNumber,
    `${borrowerDisplayName} (${borrowerLoginId})`,
    "2026-05-12"
  );

  const assetRow = page.locator("tr", { hasText: assetNumber });
  await assetRow.getByRole("button", { name: "削除" }).click();
  await expect(page.getByText("貸出中の備品は削除できません")).toBeVisible();

  await page.getByRole("button", { name: "ユーザー一覧へ" }).click();
  const userRow = page.locator("tr", { hasText: borrowerLoginId });
  await userRow.getByRole("button", { name: "削除" }).click();
  await expect(page.getByText("貸出中備品を保有するユーザーは削除できません")).toBeVisible();
});
