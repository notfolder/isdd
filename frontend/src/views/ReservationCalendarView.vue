<!--
  予約カレンダー画面コンポーネント。
  要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-FT-CANCEL-RESERVATION
  設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
  要件概要: 利用者が備品の予約一覧をカレンダー形式で確認し、自分の予約をキャンセルできる。管理者は全予約をキャンセルできる。
  設計概要: ReservationStore から予約一覧を取得してテーブル表示し、予約者本人または管理者にのみキャンセルボタンを表示する。
  呼び出し先: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR, DS-SC-AUTH-STORE-FT-LOGIN, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h5">予約状況: {{ equipment.name || equipmentId }}</h1>
        <div v-if="equipment.status">
          状態: <v-chip :color="statusColor(equipment.status)" small>{{ statusLabel(equipment.status) }}</v-chip>
        </div>
      </v-col>
      <v-col class="text-right">
        <v-btn color="primary" class="mr-2" data-testid="add-reservation-button" @click="goToNewReservation">
          予約する
        </v-btn>
        <v-btn data-testid="back-button" @click="goBack">戻る</v-btn>
      </v-col>
    </v-row>

    <v-alert v-if="reservationStore.errorMessage" type="error" class="mb-4" data-testid="error-message">
      {{ reservationStore.errorMessage }}
    </v-alert>
    <v-alert v-if="cancelError" type="error" class="mb-4" data-testid="cancel-error-message">
      {{ cancelError }}
    </v-alert>

    <v-table data-testid="reservation-table">
      <thead>
        <tr>
          <th>予約者</th>
          <th>部署</th>
          <th>開始日</th>
          <th>終了日</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in reservationStore.reservations"
          :key="r.reservation_id"
          :data-testid="`reservation-row-${r.reservation_id}`"
        >
          <td>{{ r.user_display_name }}</td>
          <td :data-testid="`dept-${r.reservation_id}`">{{ deptStore.deptNames[r.user_login_id] || '取得中...' }}</td>
          <td>{{ r.start_date }}</td>
          <td>{{ r.end_date }}</td>
          <td>
            <v-btn
              v-if="canCancel(r)"
              size="small"
              color="error"
              :data-testid="`cancel-button-${r.reservation_id}`"
              @click="handleCancel(r.reservation_id)"
            >
              キャンセル
            </v-btn>
          </td>
        </tr>
        <tr v-if="reservationStore.reservations.length === 0 && !reservationStore.loading">
          <td colspan="5" class="text-center text-medium-emphasis">予約はありません</td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
/**
 * 予約カレンダー画面のロジック。
 * 要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-FT-CANCEL-RESERVATION
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 * 呼び出し先: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useReservationStore } from '../stores/reservation.js'
import { useDeptStore } from '../stores/dept.js'
import { listEquipment } from '../api/equipment.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const reservationStore = useReservationStore()
const deptStore = useDeptStore()

const equipmentId = route.params.id
const equipment = ref({})
const cancelError = ref('')

/**
 * ステータスに対応する表示ラベルを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 */
function statusLabel(status) {
  if (status === 'loaned') return '貸出中'
  if (status === 'reserved') return '予約済み'
  return '貸出可能'
}

/**
 * ステータスに対応するチップカラーを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 */
function statusColor(status) {
  if (status === 'loaned') return 'orange'
  if (status === 'reserved') return 'blue'
  return 'green'
}

/**
 * キャンセルボタン表示可否を判定する。予約者本人または管理者のみ表示する。
 * 要件ID: RQ-FT-CANCEL-RESERVATION
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 */
function canCancel(reservation) {
  return authStore.role === 'admin' || reservation.user_login_id === authStore.loginId
}

/**
 * 予約キャンセル処理。確認後にキャンセルAPIを呼び出す。
 * 要件ID: RQ-FT-CANCEL-RESERVATION
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 */
async function handleCancel(reservationId) {
  cancelError.value = ''
  try {
    await reservationStore.removeReservation(reservationId, equipmentId)
    await loadDeptNames()
  } catch (err) {
    cancelError.value = err.response?.data?.detail || 'キャンセルに失敗しました'
  }
}

/**
 * 予約一覧の予約者部署名を並行取得する。
 * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
 */
async function loadDeptNames() {
  const loginIds = reservationStore.reservations.map((r) => r.user_login_id)
  if (loginIds.length > 0) {
    await deptStore.fetchDeptNames(loginIds)
  }
}

function goBack() {
  if (authStore.role === 'admin') {
    router.push('/admin/equipment')
  } else {
    router.push('/general/equipment')
  }
}

function goToNewReservation() {
  router.push(`/equipment/${equipmentId}/reservations/new`)
}

onMounted(async () => {
  await reservationStore.fetchReservations(equipmentId)
  await loadDeptNames()
  try {
    const res = await listEquipment()
    const found = res.data.find((e) => e.equipment_id === equipmentId)
    if (found) equipment.value = found
  } catch {
    // 備品情報取得失敗は無視
  }
})

watch(
  () => reservationStore.reservations,
  () => loadDeptNames(),
)
</script>
