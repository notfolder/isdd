<template>
  <v-layout>
    <main-navigation-bar title="備品一覧" mode="assets" />
    <v-main>
      <v-container class="py-6">
        <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4">
          {{ errorMessage }}
        </v-alert>
        <v-card>
          <v-card-title class="text-h6">備品一覧</v-card-title>
          <v-data-table
            :headers="headers"
            :items="assets"
            item-key="asset_number"
            :items-per-page="200"
          >
            <template #item.actions="{ item }">
              <v-btn v-if="isAdmin" size="small" class="mx-1" @click="goEdit(item.asset_number)">編集</v-btn>
              <v-btn v-if="isAdmin" size="small" class="mx-1" color="error" @click="removeAsset(item.asset_number)">削除</v-btn>
              <v-btn v-if="isAdmin" size="small" class="mx-1" color="primary" @click="openLoanDialog(item)">貸出登録</v-btn>
              <v-btn
                v-if="isAdmin"
                size="small"
                class="mx-1"
                color="secondary"
                @click="registerReturn(item.asset_number)"
              >
                返却登録
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>

  <v-dialog v-model="loanDialog" max-width="560">
    <v-card>
      <v-card-title>貸出登録</v-card-title>
      <v-card-text>
        <v-text-field v-model="loanTargetAssetNumber" label="資産管理番号" readonly />
        <v-select
          v-model="loanBorrowerLoginId"
          :items="borrowerOptions"
          item-title="display"
          item-value="login_id"
          label="借用者"
        />
        <v-text-field v-model="loanDate" label="貸出日 (YYYY-MM-DD)" />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="loanDialog = false">キャンセル</v-btn>
        <v-btn color="primary" @click="registerLoan">登録</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * 備品一覧/備品管理画面。
 * 要件ID: RQ-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 要件概要: 備品一覧閲覧と管理者向け行操作（編集/削除/貸出/返却）を提供する。
 * 設計概要: 一覧行末ボタンで各操作を実行し、管理者のみ更新系操作を利用できる。
 * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN, DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 */

import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import MainNavigationBar from "../components/MainNavigationBar.vue";
import { apiGet, apiSend } from "../services/api.js";

const router = useRouter();

const assets = ref([]);
const users = ref([]);
const errorMessage = ref("");

const loanDialog = ref(false);
const loanTargetAssetNumber = ref("");
const loanBorrowerLoginId = ref("");
const loanDate = ref("");

const isAdmin = computed(() => localStorage.getItem("role") === "管理者");

const headers = computed(() => {
  /**
   * ロールに応じて一覧ヘッダーを生成する。
   * 要件ID: RQ-FT-AUTHORIZE-BY-ROLE
   * 設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 要件概要: 管理者と一般ユーザーで操作権限を分離する。
   * 設計概要: 一般ユーザーには操作列を表示せず閲覧専用にする。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  const baseHeaders = [
    { title: "資産番号", key: "asset_number" },
    { title: "備品名", key: "asset_name" },
    { title: "状態", key: "loan_status" },
    { title: "借用者名", key: "borrower_name" },
  ];
  if (isAdmin.value) {
    return [...baseHeaders, { title: "操作", key: "actions", sortable: false }];
  }
  return baseHeaders;
});

const borrowerOptions = computed(() =>
  users.value.map((user) => ({
    login_id: user.login_id,
    display: `${user.display_name} (${user.login_id})`,
  }))
);

function ensureAuthenticated() {
  /**
   * 認証トークンの存在を検証する。
   * 要件ID: RQ-FT-AUTHENTICATE-USER
   * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 要件概要: 未認証ユーザーを保護画面へ入れない。
   * 設計概要: トークン未設定時はログイン画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!localStorage.getItem("token")) {
    router.push("/");
  }
}

async function loadAssets() {
  /**
   * 備品一覧を取得する。
   * 要件ID: RQ-FT-VIEW-ASSET-LIST
   * 設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 要件概要: 備品一覧に貸出状態と借用者を表示する。
   * 設計概要: `/api/assets` から一覧取得し画面表へ反映する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  const response = await apiGet("/api/assets");
  assets.value = response.items;
}

async function loadUsersForLoan() {
  /**
   * 貸出登録用ユーザー候補を取得する。
   * 要件ID: RQ-DT-BORROWER-MUST-BE-REGISTERED-USER
   * 設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 要件概要: 貸出先は登録済みユーザーのみ指定できる。
   * 設計概要: 管理者時のみユーザー一覧を取得し、貸出ダイアログ候補に利用する。
   * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!isAdmin.value) {
    users.value = [];
    return;
  }
  const response = await apiGet("/api/users");
  users.value = response.items;
}

function goEdit(assetNumber) {
  /**
   * 備品編集画面へ遷移する。
   * 要件ID: RQ-FT-UPDATE-ASSET
   * 設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
   * 要件概要: 管理者が備品を編集できる。
   * 設計概要: 行末編集ボタン押下で対象資産の編集画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!isAdmin.value) {
    errorMessage.value = "管理者のみ操作可能です";
    return;
  }
  router.push(`/assets/${assetNumber}/edit`);
}

async function removeAsset(assetNumber) {
  /**
   * 備品削除を実行する。
   * 要件ID: RQ-FT-DELETE-ASSET-WITH-LOAN-CHECK
   * 設計ID: DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK
   * 要件概要: 貸出中備品は削除できない。
   * 設計概要: 行末削除ボタン押下で削除APIを実行し、失敗時はエラー表示する。
   * 呼び出し先設計ID: DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!isAdmin.value) {
    errorMessage.value = "管理者のみ操作可能です";
    return;
  }
  try {
    await apiSend(`/api/assets/${assetNumber}`, "DELETE");
    await loadAssets();
  } catch (error) {
    errorMessage.value = String(error?.message || "備品削除に失敗しました");
  }
}

function openLoanDialog(item) {
  /**
   * 貸出登録ダイアログを開く。
   * 要件ID: RQ-FT-REGISTER-LOAN
   * 設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 要件概要: 管理者が貸出登録を実行できる。
   * 設計概要: 対象資産番号と初期貸出日を設定してダイアログを表示する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!isAdmin.value) {
    errorMessage.value = "管理者のみ操作可能です";
    return;
  }
  loanTargetAssetNumber.value = item.asset_number;
  loanBorrowerLoginId.value = item.borrower_login_id || "";
  loanDate.value = item.loan_date || new Date().toISOString().slice(0, 10);
  loanDialog.value = true;
}

async function registerLoan() {
  /**
   * 貸出登録を実行する。
   * 要件ID: RQ-FT-REGISTER-LOAN
   * 設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 要件概要: 借用者と貸出日を記録して状態を貸出中へ変更する。
   * 設計概要: ダイアログ入力値を貸出APIへ送信する。
   * 呼び出し先設計ID: DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  try {
    await apiSend(`/api/assets/${loanTargetAssetNumber.value}/loan`, "POST", {
      borrower_login_id: loanBorrowerLoginId.value,
      loan_date: loanDate.value,
    });
    loanDialog.value = false;
    await loadAssets();
  } catch (error) {
    errorMessage.value = String(error?.message || "貸出登録に失敗しました");
  }
}

async function registerReturn(assetNumber) {
  /**
   * 返却登録を実行する。
   * 要件ID: RQ-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 設計ID: DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 要件概要: 返却時に借用者と貸出日をクリアする。
   * 設計概要: 行末返却ボタン押下で返却APIを実行する。
   * 呼び出し先設計ID: DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  if (!isAdmin.value) {
    errorMessage.value = "管理者のみ操作可能です";
    return;
  }
  try {
    await apiSend(`/api/assets/${assetNumber}/return`, "POST");
    await loadAssets();
  } catch (error) {
    errorMessage.value = String(error?.message || "返却登録に失敗しました");
  }
}

onMounted(async () => {
  /**
   * 画面初期表示時のデータ読み込みを行う。
   * 要件ID: RQ-FT-VIEW-ASSET-LIST
   * 設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 要件概要: 画面表示時に備品一覧を参照できること。
   * 設計概要: 認証確認後に備品一覧と貸出候補ユーザーを読み込む。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  ensureAuthenticated();
  try {
    await loadAssets();
    await loadUsersForLoan();
  } catch (error) {
    errorMessage.value = String(error?.message || "一覧取得に失敗しました");
  }
});
</script>
