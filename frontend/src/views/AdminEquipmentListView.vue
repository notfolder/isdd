<!--
  管理者向け備品一覧画面コンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT, RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-DT-EQUIPMENT-RESERVED-STATUS
  設計ID: DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
  要件概要: 管理者が全備品と貸出状態を一覧確認し、登録・編集・削除・貸出・返却・予約状況確認操作を開始できる。予約済みステータスを表示する。貸出先に部署名を表示する。
  設計概要: EquipmentStore から備品一覧を取得してテーブル表示する。status が available または reserved の場合に貸出ボタンを表示する。DeptStore で貸出先部署名を非同期取得する。
  呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT, DS-SC-AUTH-STORE-FT-LOGIN, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID, DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h5">備品一覧</h1>
      </v-col>
      <v-col class="text-right">
        <v-btn color="secondary" class="mr-2" data-testid="manage-users-button" @click="router.push('/admin/users')">
          利用者管理
        </v-btn>
        <v-btn color="primary" class="mr-2" data-testid="add-equipment-button" @click="router.push('/admin/equipment/new')">
          備品登録
        </v-btn>
        <v-btn data-testid="logout-button" @click="handleLogout">ログアウト</v-btn>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-table data-testid="equipment-table">
      <thead>
        <tr>
          <th>備品ID</th>
          <th>備品名</th>
          <th>状態</th>
          <th>貸出先</th>
          <th>貸出日</th>
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
          <td :data-testid="`loan-user-${item.equipment_id}`">
            <template v-if="item.loan_info?.user_login_id">
              {{ item.loan_info.user_display_name }}（{{ deptStore.deptNames[item.loan_info.user_login_id] || '取得中...' }}）
            </template>
          </td>
          <td>{{ item.loan_info?.loan_date || '' }}</td>
          <td>
            <v-btn
              size="small"
              color="info"
              class="mr-1"
              :data-testid="`reservation-button-${item.equipment_id}`"
              @click="router.push(`/equipment/${item.equipment_id}/reservations`)"
            >
              予約状況
            </v-btn>
            <template v-if="item.status === 'available' || item.status === 'reserved'">
              <v-btn
                size="small"
                color="primary"
                class="mr-1"
                :data-testid="`loan-button-${item.equipment_id}`"
                @click="router.push(`/admin/equipment/${item.equipment_id}/loan`)"
              >
                貸出
              </v-btn>
              <v-btn
                size="small"
                color="secondary"
                class="mr-1"
                :data-testid="`edit-button-${item.equipment_id}`"
                @click="router.push(`/admin/equipment/${item.equipment_id}/edit`)"
              >
                編集
              </v-btn>
              <v-btn
                size="small"
                color="error"
                :data-testid="`delete-button-${item.equipment_id}`"
                @click="router.push(`/admin/equipment/${item.equipment_id}/delete`)"
              >
                削除
              </v-btn>
            </template>
            <template v-else>
              <v-btn
                size="small"
                color="warning"
                :data-testid="`return-button-${item.equipment_id}`"
                @click="router.push(`/admin/equipment/${item.equipment_id}/return`)"
              >
                返却
              </v-btn>
            </template>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
/**
 * 管理者向け備品一覧画面のロジック。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-DT-EQUIPMENT-RESERVED-STATUS, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
 * 呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useEquipmentStore } from '../stores/equipment.js'
import { useDeptStore } from '../stores/dept.js'

const router = useRouter()
const authStore = useAuthStore()
const equipmentStore = useEquipmentStore()
const deptStore = useDeptStore()
const errorMessage = ref('')

/**
 * ステータスに対応する表示ラベルを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
 */
function statusLabel(status) {
  if (status === 'loaned') return '貸出中'
  if (status === 'reserved') return '予約済み'
  return '貸出可能'
}

/**
 * ステータスに対応するチップカラーを返す。
 * 要件ID: RQ-DT-EQUIPMENT-RESERVED-STATUS
 * 設計ID: DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
 */
function statusColor(status) {
  if (status === 'loaned') return 'orange'
  if (status === 'reserved') return 'blue'
  return 'green'
}

onMounted(async () => {
  await equipmentStore.fetchEquipment()
  const loanedLoginIds = equipmentStore.equipmentList
    .filter((item) => item.loan_info?.user_login_id)
    .map((item) => item.loan_info.user_login_id)
  if (loanedLoginIds.length > 0) {
    await deptStore.fetchDeptNames(loanedLoginIds)
  }
})

/**
 * ログアウト処理。AuthStore のセッションをクリアしてログイン画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
 */
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
