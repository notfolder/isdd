<!--
  一般利用者向け備品一覧画面コンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS, RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-DT-EQUIPMENT-RESERVED-STATUS
  設計ID: DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN
  要件概要: 一般利用者が全備品と貸出状態を閲覧できる。予約済みステータスと予約状況ボタンを表示する。
  設計概要: EquipmentStore から備品一覧を取得してテーブル表示する。status='reserved' を「予約済み」として表示し、予約状況ボタンを各行に表示する。
  呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT, DS-SC-AUTH-STORE-FT-LOGIN, DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h5">備品一覧</h1>
      </v-col>
      <v-col class="text-right">
        <v-btn data-testid="logout-button" @click="handleLogout">ログアウト</v-btn>
      </v-col>
    </v-row>

    <v-table data-testid="equipment-table">
      <thead>
        <tr>
          <th>備品ID</th>
          <th>備品名</th>
          <th>状態</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in equipmentStore.equipmentList" :key="item.equipment_id" :data-testid="`equipment-row-${item.equipment_id}`">
          <td>{{ item.equipment_id }}</td>
          <td>{{ item.name }}</td>
          <td>
            <v-chip :color="statusColor(item.status)" small :data-testid="`status-chip-${item.equipment_id}`">
              {{ statusLabel(item.status) }}
            </v-chip>
          </td>
          <td>
            <v-btn
              size="small"
              color="info"
              :data-testid="`reservation-button-${item.equipment_id}`"
              @click="router.push(`/equipment/${item.equipment_id}/reservations`)"
            >
              予約状況
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
/**
 * 一般利用者向け備品一覧画面のロジック。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS, RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN
 * 呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useEquipmentStore } from '../stores/equipment.js'

const router = useRouter()
const authStore = useAuthStore()
const equipmentStore = useEquipmentStore()

/**
 * ステータスに対応する表示ラベルを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN
 */
function statusLabel(status) {
  if (status === 'loaned') return '貸出中'
  if (status === 'reserved') return '予約済み'
  return '貸出可能'
}

/**
 * ステータスに対応するチップカラーを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN
 */
function statusColor(status) {
  if (status === 'loaned') return 'orange'
  if (status === 'reserved') return 'blue'
  return 'green'
}

onMounted(async () => {
  await equipmentStore.fetchEquipment()
})

/**
 * ログアウト処理。AuthStore のセッションをクリアしてログイン画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN
 */
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
