<!--
  一般利用者向け備品一覧画面コンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS
  設計ID: DS-VC-GENERAL-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
  要件概要: 一般利用者が全備品と貸出状態を閲覧できる。操作ボタン（登録・編集・削除・貸出）は表示しない。
  設計概要: EquipmentStore から備品一覧を取得してテーブル表示する。管理者向けボタンを一切含まない。
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
        <v-btn data-testid="logout-button" @click="handleLogout">ログアウト</v-btn>
      </v-col>
    </v-row>

    <v-table data-testid="equipment-table">
      <thead>
        <tr>
          <th>備品ID</th>
          <th>備品名</th>
          <th>状態</th>
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
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
/**
 * 一般利用者向け備品一覧画面のロジック。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS
 * 設計ID: DS-VC-GENERAL-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
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

onMounted(async () => {
  await equipmentStore.fetchEquipment()
})

/**
 * ログアウト処理。AuthStore のセッションをクリアしてログイン画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-VC-GENERAL-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
 */
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
