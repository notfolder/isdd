/**
 * E2Eテスト - 備品管理・貸出管理アプリ
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-FT-LOGIN, RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, 
 *           RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST, 
 *           RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST, 
 *           RQ-FT-LOGOUT, RQ-NF-ACCESS-CONTROL
 *   設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ITEM-LIST-SCREEN-UI-ITEM-LIST-SCREEN,
 *           DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN, 
 *           DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 *   要件概要: システム全体のE2Eテストを実行する
 *   設計概要: Playwrightを使用して全機能の動作を確認する
 */

import { test, expect, Page } from '@playwright/test';

// テストデータ
const ADMIN_USER = {
  userId: 'admin',
  password: 'admin',
  role: '管理者'
};

const GENERAL_USER = {
  userId: 'testuser',
  password: 'testpass',
  name: 'テストユーザー',
  role: '一般利用者'
};

const TEST_ITEM = {
  assetNumber: 'E2E-001',
  name: 'E2Eテスト備品'
};

const TEST_ITEM_2 = {
  assetNumber: 'E2E-002',
  name: 'E2Eテスト備品2'
};

/**
 * ログイン処理のヘルパー関数
 * 
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
 */
async function login(page: Page, userId: string, password: string) {
  await page.goto('/login');
  await page.fill('input[type="text"]', userId);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
}

/**
 * ログアウト処理のヘルパー関数
 * 
 * 要件ID: RQ-FT-LOGOUT
 * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
 */
async function logout(page: Page) {
  await page.click('button:has-text("ログアウト")');
}

test.describe('E2Eテスト - 備品管理・貸出管理アプリ', () => {
  
  /**
   * E2E-001: ログイン機能テスト
   * 
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
   * 要件概要: ユーザーIDとパスワードでログインできる
   * 設計概要: 正しい認証情報でログインし、備品一覧画面に遷移することを確認する
   */
  test('E2E-001: 管理者でログインできる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    
    // ログイン成功後、備品一覧画面に遷移することを確認
    await expect(page).toHaveURL('/items');
    await expect(page.locator('text=備品一覧')).toBeVisible();
    await expect(page.locator(`text=${ADMIN_USER.userId} (${ADMIN_USER.role})`)).toBeVisible();
  });
  
  /**
   * E2E-002: 備品一覧表示テスト
   * 
   * 要件ID: RQ-FT-VIEW-ITEM-LIST
   * 設計ID: DS-IF-ITEM-LIST-SCREEN-UI-ITEM-LIST-SCREEN
   * 要件概要: 備品一覧と貸出状況を表示できる
   * 設計概要: 備品一覧画面で備品リストが表示されることを確認する
   */
  test('E2E-002: 備品一覧を表示できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items');
    
    // 備品一覧テーブルが表示されることを確認
    await expect(page.locator('text=資産管理番号')).toBeVisible();
    await expect(page.locator('text=備品名称')).toBeVisible();
    await expect(page.locator('text=ステータス')).toBeVisible();
    await expect(page.locator('text=借り主')).toBeVisible();
  });
  
  /**
   * E2E-003: 備品登録テスト
   * 
   * 要件ID: RQ-FT-REGISTER-ITEM
   * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
   * 要件概要: 管理者が備品を新規登録できる
   * 設計概要: 備品管理画面で新規登録ダイアログを開き、備品を登録することを確認する
   */
  test('E2E-003: 備品を登録できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items/manage');
    
    // 新規登録ボタンをクリック
    await page.click('button:has-text("新規登録")');
    
    // 備品情報を入力
    await page.fill('input[label="資産管理番号"]', TEST_ITEM.assetNumber);
    await page.fill('input[label="備品名称"]', TEST_ITEM.name);
    
    // 登録ボタンをクリック
    await page.click('button:has-text("登録")');
    
    // 登録された備品がテーブルに表示されることを確認
    await expect(page.locator(`text=${TEST_ITEM.assetNumber}`)).toBeVisible();
    await expect(page.locator(`text=${TEST_ITEM.name}`)).toBeVisible();
  });
  
  /**
   * E2E-004: 備品編集テスト
   * 
   * 要件ID: RQ-FT-EDIT-ITEM
   * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
   * 要件概要: 管理者が備品情報を編集できる
   * 設計概要: 備品管理画面で編集ダイアログを開き、備品名称を変更することを確認する
   */
  test('E2E-004: 備品を編集できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items/manage');
    
    // 既存の備品の編集ボタンをクリック（先にテスト備品を登録）
    await page.click('button:has-text("新規登録")');
    await page.fill('input[label="資産管理番号"]', TEST_ITEM_2.assetNumber);
    await page.fill('input[label="備品名称"]', TEST_ITEM_2.name);
    await page.click('button:has-text("登録")');
    
    // 編集ボタンをクリック（TEST_ITEM_2の行の編集アイコン）
    const row = page.locator(`tr:has-text("${TEST_ITEM_2.assetNumber}")`);
    await row.locator('button[aria-label="edit"]').first().click();
    
    // 備品名称を変更
    const updatedName = 'E2Eテスト備品2（更新済み）';
    await page.fill('input[label="備品名称"]', updatedName);
    
    // 更新ボタンをクリック
    await page.click('button:has-text("更新")');
    
    // 更新された備品名称が表示されることを確認
    await expect(page.locator(`text=${updatedName}`)).toBeVisible();
  });
  
  /**
   * E2E-005: 備品削除テスト
   * 
   * 要件ID: RQ-FT-DELETE-ITEM
   * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
   * 要件概要: 管理者が備品を削除できる
   * 設計概要: 備品管理画面で削除確認ダイアログを開き、備品を削除することを確認する
   */
  test('E2E-005: 備品を削除できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items/manage');
    
    // テスト用備品を登録
    const deleteItem = { assetNumber: 'E2E-DEL', name: '削除テスト備品' };
    await page.click('button:has-text("新規登録")');
    await page.fill('input[label="資産管理番号"]', deleteItem.assetNumber);
    await page.fill('input[label="備品名称"]', deleteItem.name);
    await page.click('button:has-text("登録")');
    
    // 削除ボタンをクリック
    const row = page.locator(`tr:has-text("${deleteItem.assetNumber}")`);
    await row.locator('button[aria-label="delete"]').first().click();
    
    // 削除確認ダイアログで削除ボタンをクリック
    await page.click('button:has-text("削除")');
    
    // 削除された備品が表示されないことを確認
    await expect(page.locator(`text=${deleteItem.assetNumber}`)).not.toBeVisible();
  });
  
  /**
   * E2E-006: 備品貸出テスト
   * 
   * 要件ID: RQ-FT-LEND-ITEM
   * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
   * 要件概要: 管理者が備品を貸し出せる
   * 設計概要: 備品管理画面で貸出ダイアログを開き、借り主を設定して貸出することを確認する
   */
  test('E2E-006: 備品を貸出できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items/manage');
    
    // テスト用備品を登録
    const lendItem = { assetNumber: 'E2E-LEND', name: '貸出テスト備品' };
    await page.click('button:has-text("新規登録")');
    await page.fill('input[label="資産管理番号"]', lendItem.assetNumber);
    await page.fill('input[label="備品名称"]', lendItem.name);
    await page.click('button:has-text("登録")');
    
    // 貸出ボタンをクリック
    const row = page.locator(`tr:has-text("${lendItem.assetNumber}")`);
    await row.locator('button[aria-label="lend"]').first().click();
    
    // 借り主を入力
    const borrower = 'テスト太郎';
    await page.fill('input[label="借り主"]', borrower);
    
    // 貸出ボタンをクリック
    await page.click('button:has-text("貸出")');
    
    // 貸出中ステータスと借り主が表示されることを確認
    await expect(page.locator(`tr:has-text("${lendItem.assetNumber}") >> text=貸出中`)).toBeVisible();
    await expect(page.locator(`tr:has-text("${lendItem.assetNumber}") >> text=${borrower}`)).toBeVisible();
  });
  
  /**
   * E2E-007: 備品返却テスト
   * 
   * 要件ID: RQ-FT-RETURN-ITEM
   * 設計ID: DS-IF-ITEM-MANAGEMENT-SCREEN-UI-ITEM-MANAGEMENT-SCREEN
   * 要件概要: 管理者が備品を返却できる
   * 設計概要: 備品管理画面で返却確認ダイアログを開き、返却することを確認する
   */
  test('E2E-007: 備品を返却できる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/items/manage');
    
    // テスト用備品を登録して貸出
    const returnItem = { assetNumber: 'E2E-RETURN', name: '返却テスト備品' };
    await page.click('button:has-text("新規登録")');
    await page.fill('input[label="資産管理番号"]', returnItem.assetNumber);
    await page.fill('input[label="備品名称"]', returnItem.name);
    await page.click('button:has-text("登録")');
    
    // 貸出処理
    let row = page.locator(`tr:has-text("${returnItem.assetNumber}")`);
    await row.locator('button[aria-label="lend"]').first().click();
    await page.fill('input[label="借り主"]', 'テスト次郎');
    await page.click('button:has-text("貸出")');
    
    // 返却ボタンをクリック
    row = page.locator(`tr:has-text("${returnItem.assetNumber}")`);
    await row.locator('button[aria-label="return"]').first().click();
    
    // 返却確認ダイアログで返却ボタンをクリック
    await page.click('button:has-text("返却")');
    
    // 利用可能ステータスになり、借り主が空になることを確認
    await expect(page.locator(`tr:has-text("${returnItem.assetNumber}") >> text=利用可能`)).toBeVisible();
    await expect(page.locator(`tr:has-text("${returnItem.assetNumber}") >> text=テスト次郎`)).not.toBeVisible();
  });
  
  /**
   * E2E-008: 利用者一覧表示テスト
   * 
   * 要件ID: RQ-FT-VIEW-USER-LIST
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 管理者が利用者一覧を表示できる
   * 設計概要: 利用者管理画面で利用者リストが表示されることを確認する
   */
  test('E2E-008: 利用者一覧を表示できる（管理者のみ）', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/users');
    
    // 利用者一覧テーブルが表示されることを確認
    await expect(page.locator('text=ユーザーID')).toBeVisible();
    await expect(page.locator('text=氏名')).toBeVisible();
    await expect(page.locator('text=権限')).toBeVisible();
    
    // 初期管理者（admin）が表示されることを確認
    await expect(page.locator(`text=${ADMIN_USER.userId}`)).toBeVisible();
  });
  
  /**
   * E2E-009: 利用者登録テスト
   * 
   * 要件ID: RQ-FT-REGISTER-USER
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 管理者が利用者を新規登録できる
   * 設計概要: 利用者管理画面で新規登録ダイアログを開き、利用者を登録することを確認する
   */
  test('E2E-009: 利用者を登録できる（管理者のみ）', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/users');
    
    // 新規登録ボタンをクリック
    await page.click('button:has-text("新規登録")');
    
    // 利用者情報を入力
    await page.fill('input[label="ユーザーID"]', GENERAL_USER.userId);
    await page.fill('input[label="氏名"]', GENERAL_USER.name);
    await page.fill('input[type="password"]', GENERAL_USER.password);
    await page.selectOption('select[label="権限"]', GENERAL_USER.role);
    
    // 登録ボタンをクリック
    await page.click('button:has-text("登録")');
    
    // 登録された利用者がテーブルに表示されることを確認
    await expect(page.locator(`text=${GENERAL_USER.userId}`)).toBeVisible();
    await expect(page.locator(`text=${GENERAL_USER.name}`)).toBeVisible();
  });
  
  /**
   * E2E-010: 利用者編集テスト
   * 
   * 要件ID: RQ-FT-EDIT-USER
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 管理者が利用者情報を編集できる
   * 設計概要: 利用者管理画面で編集ダイアログを開き、利用者情報を変更することを確認する
   */
  test('E2E-010: 利用者を編集できる（管理者のみ）', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/users');
    
    // テストユーザーが存在しない場合は作成
    const testUserId = 'edittest';
    const isUserExists = await page.locator(`text=${testUserId}`).isVisible();
    if (!isUserExists) {
      await page.click('button:has-text("新規登録")');
      await page.fill('input[label="ユーザーID"]', testUserId);
      await page.fill('input[label="氏名"]', '編集テストユーザー');
      await page.fill('input[type="password"]', 'testpass');
      await page.selectOption('select[label="権限"]', '一般利用者');
      await page.click('button:has-text("登録")');
    }
    
    // 編集ボタンをクリック
    const row = page.locator(`tr:has-text("${testUserId}")`);
    await row.locator('button[aria-label="edit"]').first().click();
    
    // 氏名を変更
    const updatedName = '編集テストユーザー（更新済み）';
    await page.fill('input[label="氏名"]', updatedName);
    
    // 更新ボタンをクリック
    await page.click('button:has-text("更新")');
    
    // 更新された氏名が表示されることを確認
    await expect(page.locator(`text=${updatedName}`)).toBeVisible();
  });
  
  /**
   * E2E-011: 利用者削除テスト
   * 
   * 要件ID: RQ-FT-DELETE-USER
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 管理者が利用者を削除できる
   * 設計概要: 利用者管理画面で削除確認ダイアログを開き、利用者を削除することを確認する
   */
  test('E2E-011: 利用者を削除できる（管理者のみ）', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/users');
    
    // テスト用利用者を登録
    const deleteUser = { userId: 'deltest', name: '削除テストユーザー', password: 'testpass' };
    await page.click('button:has-text("新規登録")');
    await page.fill('input[label="ユーザーID"]', deleteUser.userId);
    await page.fill('input[label="氏名"]', deleteUser.name);
    await page.fill('input[type="password"]', deleteUser.password);
    await page.selectOption('select[label="権限"]', '一般利用者');
    await page.click('button:has-text("登録")');
    
    // 削除ボタンをクリック
    const row = page.locator(`tr:has-text("${deleteUser.userId}")`);
    await row.locator('button[aria-label="delete"]').first().click();
    
    // 削除確認ダイアログで削除ボタンをクリック
    await page.click('button:has-text("削除")');
    
    // 削除された利用者が表示されないことを確認
    await expect(page.locator(`text=${deleteUser.userId}`)).not.toBeVisible();
  });
  
  /**
   * E2E-012: ログアウト機能テスト
   * 
   * 要件ID: RQ-FT-LOGOUT
   * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
   * 要件概要: ログアウトしてログイン画面に戻れる
   * 設計概要: ログアウトボタンをクリックし、ログイン画面に遷移することを確認する
   */
  test('E2E-012: ログアウトできる', async ({ page }) => {
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await expect(page).toHaveURL('/items');
    
    // ログアウトボタンをクリック
    await logout(page);
    
    // ログイン画面に遷移することを確認
    await expect(page).toHaveURL('/login');
    await expect(page.locator('text=備品管理・貸出管理システム')).toBeVisible();
  });
  
  /**
   * E2E-013: アクセス制御テスト
   * 
   * 要件ID: RQ-NF-ACCESS-CONTROL
   * 設計ID: DS-CL-ROUTER-FT-LOGIN
   * 要件概要: 一般利用者は管理者専用画面にアクセスできない
   * 設計概要: 一般利用者でログインし、管理者専用画面へのアクセスが制限されることを確認する
   */
  test('E2E-013: 一般利用者は管理者専用画面にアクセスできない', async ({ page }) => {
    // まず管理者で一般利用者を作成
    await login(page, ADMIN_USER.userId, ADMIN_USER.password);
    await page.goto('/users');
    
    const generalUser = { userId: 'generaluser', name: '一般テストユーザー', password: 'testpass' };
    const isUserExists = await page.locator(`text=${generalUser.userId}`).isVisible();
    if (!isUserExists) {
      await page.click('button:has-text("新規登録")');
      await page.fill('input[label="ユーザーID"]', generalUser.userId);
      await page.fill('input[label="氏名"]', generalUser.name);
      await page.fill('input[type="password"]', generalUser.password);
      await page.selectOption('select[label="権限"]', '一般利用者');
      await page.click('button:has-text("登録")');
    }
    
    // ログアウト
    await logout(page);
    
    // 一般利用者でログイン
    await login(page, generalUser.userId, generalUser.password);
    
    // 備品管理ボタンが表示されないことを確認
    await expect(page.locator('button:has-text("備品管理")')).not.toBeVisible();
    
    // 利用者管理ボタンが表示されないことを確認
    await expect(page.locator('button:has-text("利用者管理")')).not.toBeVisible();
    
    // 直接URLで管理者専用画面にアクセスしようとすると備品一覧にリダイレクトされることを確認
    await page.goto('/items/manage');
    await expect(page).toHaveURL('/items');
    
    await page.goto('/users');
    await expect(page).toHaveURL('/items');
  });
  
  /**
   * E2E-014: エラーハンドリングテスト
   * 
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
   * 要件概要: 誤った認証情報でログインできない
   * 設計概要: 無効なユーザーIDとパスワードでログインを試み、エラーメッセージが表示されることを確認する
   */
  test('E2E-014: 誤った認証情報でログインできない', async ({ page }) => {
    await page.goto('/login');
    
    // 誤ったユーザーIDとパスワードを入力
    await page.fill('input[type="text"]', 'invaliduser');
    await page.fill('input[type="password"]', 'invalidpass');
    await page.click('button[type="submit"]');
    
    // エラーメッセージが表示されることを確認
    await expect(page.locator('text=ユーザーIDまたはパスワードが正しくありません')).toBeVisible();
    
    // ログイン画面に留まることを確認
    await expect(page).toHaveURL('/login');
  });
  
});
