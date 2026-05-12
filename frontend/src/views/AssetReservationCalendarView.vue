<template>
  <v-layout>
    <main-navigation-bar title="備品予約カレンダー" mode="assets" />
    <v-main>
      <v-container class="py-6">
        <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4">
          {{ errorMessage }}
        </v-alert>

        <v-card class="mb-4">
          <v-card-title class="text-h6">対象備品: {{ assetNumber }}</v-card-title>
          <v-card-text>
            <div class="d-flex align-center ga-3 mb-4">
              <v-btn variant="outlined" @click="moveMonth(-1)">前月</v-btn>
              <span class="text-subtitle-1">{{ targetYearMonth }}</span>
              <v-btn variant="outlined" @click="moveMonth(1)">次月</v-btn>
              <v-spacer />
              <v-btn variant="tonal" @click="goBack">備品一覧へ戻る</v-btn>
            </div>

            <v-data-table
              :headers="reservationHeaders"
              :items="reservations"
              item-key="reservation_id"
              :items-per-page="200"
            >
              <template #item.actions="{ item }">
                <v-btn
                  v-if="canCancel(item)"
                  size="small"
                  color="error"
                  variant="tonal"
                  @click="cancelReservation(item.reservation_id)"
                >
                  取消
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title class="text-h6">予約登録</v-card-title>
          <v-card-text>
            <v-text-field v-model="startDate" label="予約開始日 (YYYY-MM-DD)" />
            <v-text-field v-model="endDate" label="予約終了日 (YYYY-MM-DD)" />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="registerReservation">予約登録</v-btn>
          </v-card-actions>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
/**
 * 備品予約カレンダー画面。
 * 要件ID: RQ-UI-ASSET-RESERVATION-CALENDAR-SCREEN
 * 設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
 * 要件概要: 対象備品の月次予約確認、予約登録、予約取消を行えること。
 * 設計概要: 月次一覧取得APIと登録/取消APIを利用して予約操作を提供する。
 * 呼び出し先設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR, DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION, DS-FN-CANCEL-RESERVATION-FT-CANCEL-RESERVATION
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
 */

import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import MainNavigationBar from "../components/MainNavigationBar.vue";
import { apiGet, apiSend } from "../services/api.js";

const route = useRoute();
const router = useRouter();

const assetNumber = computed(() => String(route.params.assetNumber || ""));
const targetYearMonth = ref(new Date().toISOString().slice(0, 7));
const reservations = ref([]);
const startDate = ref(new Date().toISOString().slice(0, 10));
const endDate = ref(new Date().toISOString().slice(0, 10));
const errorMessage = ref("");
let latestReservationLoadToken = 0;

const reservationHeaders = [
  { title: "予約ID", key: "reservation_id" },
  { title: "予約期間", key: "period" },
  { title: "予約者", key: "reserver_name" },
  { title: "予約者部署名", key: "reserver_department_display" },
  { title: "状態", key: "reservation_status" },
  { title: "操作", key: "actions", sortable: false },
];

const currentLoginId = computed(() => localStorage.getItem("login_id") || "");
const isAdmin = computed(() => localStorage.getItem("role") === "管理者");

function composeReservationDepartmentDisplay(departmentName, displayStatus) {
  /**
   * 予約者部署名の表示文字列を決定する。
   * 要件ID: RQ-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 要件概要: 取得中・成功・不明の表示を予約一覧でも切り替える。
   * 設計概要: 部署名取得状態に応じて表示文字列を返す。
   * 呼び出し先設計ID: なし
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  if (displayStatus === "部署名") {
    return departmentName || "部署名不明";
  }
  return displayStatus || "取得しています...";
}

async function resolveReservationDepartments(loadToken) {
  /**
   * 予約一覧の部署名を非同期解決して反映する。
   * 要件ID: RQ-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 要件概要: 予約一覧を先に表示し、部署名は非同期で更新する。
   * 設計概要: 予約者login_idをまとめて部署解決APIへ送信し、表示状態を上書きする。
   * 呼び出し先設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
   * 呼び出し元設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   */

  const loginIds = [
    ...new Set(
      reservations.value
        .map((item) => item.reserver_login_id)
        .filter((loginId) => Boolean(loginId))
    ),
  ];
  if (!loginIds.length) {
    return;
  }

  try {
    const response = await apiSend("/api/departments/resolve", "POST", {
      login_ids: loginIds,
    });
    if (loadToken !== latestReservationLoadToken) {
      return;
    }

    const resolvedMap = new Map(
      (response.items || [])
        .map((item) => [String(item.login_id || "").trim(), item])
        .filter(([loginId]) => Boolean(loginId))
    );

    reservations.value = reservations.value.map((item) => {
      const reserverLoginId = item.reserver_login_id || "";
      const resolved = resolvedMap.get(reserverLoginId);
      const departmentName = String(resolved?.department_name || "");
      const displayStatus = String(resolved?.department_display_status || "部署名不明");
      return {
        ...item,
        reserver_department_name: departmentName,
        reserver_department_display_status: displayStatus,
        reserver_department_display: composeReservationDepartmentDisplay(
          departmentName,
          displayStatus
        ),
      };
    });
  } catch (_error) {
    if (loadToken !== latestReservationLoadToken) {
      return;
    }

    reservations.value = reservations.value.map((item) => ({
      ...item,
      reserver_department_name: "",
      reserver_department_display_status: "部署名不明",
      reserver_department_display: "部署名不明",
    }));
  }
}

function goBack() {
  /**
   * 備品一覧へ戻る。
   * 要件ID: RQ-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   * 設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   * 要件概要: 予約画面から一覧画面へ戻れること。
   * 設計概要: 戻る操作で備品一覧画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  router.push("/assets");
}

function shiftYearMonth(baseYearMonth, diff) {
  /**
   * 対象年月を月単位で移動する。
   * 要件ID: RQ-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 要件概要: 月次単位で予約情報を確認できること。
   * 設計概要: yyyy-mm を Date へ変換して前月/次月を計算する。
   * 呼び出し先設計ID: なし
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  const [year, month] = baseYearMonth.split("-").map((value) => Number(value));
  const dateValue = new Date(year, month - 1 + diff, 1);
  return `${dateValue.getFullYear()}-${String(dateValue.getMonth() + 1).padStart(2, "0")}`;
}

async function loadReservations() {
  /**
   * 予約カレンダー情報を読み込む。
   * 要件ID: RQ-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 要件概要: 予約期間、予約者、部署名、状態を月次で参照できること。
   * 設計概要: year_month付きAPIを呼び出し、画面表示用項目へ整形する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  const response = await apiGet(
    `/api/assets/${assetNumber.value}/reservations?year_month=${targetYearMonth.value}`
  );
  latestReservationLoadToken += 1;
  const currentLoadToken = latestReservationLoadToken;
  reservations.value = (response.items || []).map((item) => {
    const departmentName = item.reserver_department_name || "";
    const displayStatus = item.reserver_department_display_status || "";
    return {
      ...item,
      period: `${item.start_date}〜${item.end_date}`,
      reserver_department_name: departmentName,
      reserver_department_display_status: displayStatus,
      reserver_department_display: composeReservationDepartmentDisplay(
        departmentName,
        displayStatus
      ),
    };
  });
  void resolveReservationDepartments(currentLoadToken);
}

function moveMonth(diff) {
  /**
   * 表示月を変更して再読み込みする。
   * 要件ID: RQ-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 要件概要: 前月/次月へ切り替えて予約状況を確認できること。
   * 設計概要: 表示月更新後に予約一覧取得を再実行する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  targetYearMonth.value = shiftYearMonth(targetYearMonth.value, diff);
  loadReservations().catch((error) => {
    errorMessage.value = String(error?.message || "予約一覧取得に失敗しました");
  });
}

function canCancel(item) {
  /**
   * 予約取消ボタンの表示可否を判定する。
   * 要件ID: RQ-FT-CANCEL-RESERVATION
   * 設計ID: DS-FN-CANCEL-RESERVATION-FT-CANCEL-RESERVATION
   * 要件概要: 本人または管理者のみ予約取消を実行できること。
   * 設計概要: 管理者または予約者本人の場合にのみ取消ボタンを表示する。
   * 呼び出し先設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  return isAdmin.value || item.reserver_login_id === currentLoginId.value;
}

async function registerReservation() {
  /**
   * 予約登録を実行する。
   * 要件ID: RQ-FT-REGISTER-RESERVATION
   * 設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION
   * 要件概要: 予約開始日/終了日を指定して本人予約を登録できること。
   * 設計概要: ログインIDを予約者として登録APIへ送信し、成功後に再取得する。
   * 呼び出し先設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend(`/api/assets/${assetNumber.value}/reservations`, "POST", {
      reserver_login_id: currentLoginId.value,
      start_date: startDate.value,
      end_date: endDate.value,
    });
    await loadReservations();
  } catch (error) {
    errorMessage.value = String(error?.message || "予約登録に失敗しました");
  }
}

async function cancelReservation(reservationId) {
  /**
   * 予約取消を実行する。
   * 要件ID: RQ-FT-CANCEL-RESERVATION
   * 設計ID: DS-FN-CANCEL-RESERVATION-FT-CANCEL-RESERVATION
   * 要件概要: 本人または管理者が予約を取り消せること。
   * 設計概要: 取消APIを呼び出し、成功後に予約一覧を再取得する。
   * 呼び出し先設計ID: DS-FN-CANCEL-RESERVATION-FT-CANCEL-RESERVATION
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend(`/api/reservations/${reservationId}`, "DELETE");
    await loadReservations();
  } catch (error) {
    errorMessage.value = String(error?.message || "予約取消に失敗しました");
  }
}

onMounted(async () => {
  /**
   * 画面初期表示時に予約一覧を読み込む。
   * 要件ID: RQ-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 要件概要: 画面表示時に対象備品の予約情報を確認できること。
   * 設計概要: 認証確認後に当月の予約一覧を取得する。
   * 呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
   * 呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
   */

  if (!localStorage.getItem("token")) {
    router.push("/");
    return;
  }

  try {
    await loadReservations();
  } catch (error) {
    errorMessage.value = String(error?.message || "予約一覧取得に失敗しました");
  }
});
</script>
