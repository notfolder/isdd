<!--
  管理者向け備品一覧画面コンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-VC-ADMIN-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
  要件概要: 管理者が全備品と貸出状態を一覧確認し、登録・編集・削除・貸出・返却操作を開始できる。
  設計概要: EquipmentStore から備品一覧を取得してテーブル表示し、状態に応じた操作ボタンを表示する。
  呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT, DS-SC-AUTH-STORE-FT-LOGIN
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
            <v-chip :color="item.status === 'loaned' ? 'orange' : 'green'" small>
              {{ item.status === 'loaned' ? '貸出中' : '貸出可能' }}
            </v-chip>
          </td>
          <td>{{ item.loan_info?.user_display_name || '' }}</td>
          <td>{{ item.loan_info?.loan_date || '' }}</td>
          <td>
            <template v-if="item.status === 'available'">
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
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-VC-ADMIN-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
 * 呼び出し先: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useEquipmentStore } from '../stores/equipment.js'

const router = useRouter()
const authStore = useAuthStore()
const equipmentStore = useEquipmentStore()
const errorMessage = ref('')

onMounted(async () => {
  await equipmentStore.fetchEquipment()
})

/**
 * ログアウト処理。AuthStore のセッションをクリアしてログイン画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-VC-ADMIN-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
 */
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
