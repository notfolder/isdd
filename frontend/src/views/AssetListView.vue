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
              <v-btn size="small" class="mx-1" color="info" @click="goReservation(item.asset_number)">
                予約
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
        <v-text-field v-model="returnDueDate" label="返却予定日 (YYYY-MM-DD)" />
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
 * 要件ID: RQ-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
 * 設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
 * 要件概要: 備品一覧で部署表示と予約導線を提供し、管理者は貸出返却も実行できる。
 * 設計概要: 一覧行末で予約遷移と管理者操作を提供し、部署表示状態を描画する。
 * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE, DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN, DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
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
const returnDueDate = ref("");

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
    { title: "借用者部署名", key: "borrower_department_display" },
    { title: "操作", key: "actions", sortable: false },
  ];
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
   * 要件ID: RQ-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
   * 設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
   * 要件概要: 備品一覧に借用者部署名と表示状態を含めて表示する。
   * 設計概要: `/api/assets` 取得結果を部署表示用項目へ整形して画面へ反映する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   */

  const response = await apiGet("/api/assets");
  assets.value = (response.items || []).map((item) => ({
    ...item,
    borrower_department_display:
      !item.borrower_login_id
        ? "-"
        : item.borrower_department_display_status === "部署名"
        ? item.borrower_department_name
        : (item.borrower_department_display_status || "取得しています..."),
  }));
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
   * 要件ID: RQ-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
   * 設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
   * 要件概要: 管理者が返却予定日付きで貸出登録を実行できる。
   * 設計概要: 対象資産と日付初期値を設定して貸出ダイアログを表示する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   */

  if (!isAdmin.value) {
    errorMessage.value = "管理者のみ操作可能です";
    return;
  }
  loanTargetAssetNumber.value = item.asset_number;
  loanBorrowerLoginId.value = item.borrower_login_id || "";
  loanDate.value = item.loan_date || new Date().toISOString().slice(0, 10);
  returnDueDate.value = item.return_due_date || new Date().toISOString().slice(0, 10);
  loanDialog.value = true;
}

function goReservation(assetNumber) {
  /**
   * 予約カレンダー画面へ遷移する。
   * 要件ID: RQ-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   * 設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   * 要件概要: 一覧行末の予約ボタンから対象備品の予約画面へ遷移できる。
   * 設計概要: 資産管理番号をルート引数として予約カレンダー画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   */

  router.push(`/assets/${assetNumber}/reservations`);
}

async function registerLoan() {
  /**
   * 貸出登録を実行する。
   * 要件ID: RQ-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
   * 設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
   * 要件概要: 借用者・貸出日・返却予定日を記録して貸出登録する。
   * 設計概要: ダイアログ入力値を貸出APIへ送信し、成功後に一覧を再取得する。
   * 呼び出し先設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   */

  try {
    await apiSend(`/api/assets/${loanTargetAssetNumber.value}/loan`, "POST", {
      borrower_login_id: loanBorrowerLoginId.value,
      loan_date: loanDate.value,
      return_due_date: returnDueDate.value,
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
   * 要件ID: RQ-FT-DELETE-LOANED-RESERVATION-ON-RETURN
   * 設計ID: DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN
   * 要件概要: 返却時に貸出済み予約を削除し、状態を貸出可能へ戻す。
   * 設計概要: 行末返却ボタン押下で返却APIを実行する。
   * 呼び出し先設計ID: DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
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
   * 要件ID: RQ-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
   * 設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
   * 要件概要: 画面初期表示時に部署表示付きの備品一覧を参照できること。
   * 設計概要: 認証確認後に備品一覧と貸出候補ユーザーを読み込む。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
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
