<!--
  備品一覧画面コンポーネント。
  要件ID: RQ-UI-EQUIPMENT-LIST-SCREEN / 設計ID: DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN
  要件概要: 全備品の状態・貸出情報を一覧表示する。管理者は貸出/返却/削除/登録操作を行える。
  設計概要: EquipmentListView。管理者にはボタンを表示、一般社員は閲覧のみ。
-->
<template>
  <v-container>
    <v-row class="mb-3" align="center">
      <v-col><span class="text-h6">備品一覧</span></v-col>
      <v-col cols="auto" v-if="auth.isAdmin">
        <v-btn color="primary" to="/equipment/new">+ 備品登録</v-btn>
        <v-btn color="secondary" to="/users" class="ml-2">ユーザー管理</v-btn>
      </v-col>
      <v-col cols="auto">
        <v-btn variant="text" @click="auth.logout(); $router.push('/login')">ログアウト</v-btn>
      </v-col>
    </v-row>

    <v-alert v-if="errorMsg" type="error" class="mb-3">{{ errorMsg }}</v-alert>

    <v-table>
      <thead>
        <tr>
          <th>管理番号</th><th>備品名</th><th>状態</th>
          <th>貸出先</th><th>返却予定日</th>
          <th v-if="auth.isAdmin">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="eq in equipmentList" :key="eq.management_number">
          <td>{{ eq.management_number }}</td>
          <td>{{ eq.name }}</td>
          <td>
            <v-chip :color="eq.status === '在庫中' ? 'green' : 'orange'" size="small">
              {{ eq.status }}
            </v-chip>
          </td>
          <td>{{ eq.lending_info?.user_name || '' }}</td>
          <td>{{ eq.lending_info?.expected_return_date || '' }}</td>
          <td v-if="auth.isAdmin">
            <v-btn
              v-if="eq.status === '在庫中'"
              size="small" color="primary" class="mr-1"
              @click="openLendModal(eq)"
            >貸出</v-btn>
            <v-btn
              v-if="eq.status === '貸出中'"
              size="small" color="warning" class="mr-1"
              @click="openReturnDialog(eq)"
            >返却</v-btn>
            <v-btn size="small" color="error" @click="handleDelete(eq.management_number)">削除</v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>

    <LendingModal
      v-if="lendTarget"
      :equipment="lendTarget"
      :users="userList"
      @close="lendTarget = null"
      @submitted="refresh"
    />
    <ReturnDialog
      v-if="returnTarget"
      :equipment="returnTarget"
      @close="returnTarget = null"
      @submitted="refresh"
    />
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { listEquipment, deleteEquipment } from '../api/equipment.js'
import { listUsers } from '../api/users.js'
import LendingModal from '../components/LendingModal.vue'
import ReturnDialog from '../components/ReturnDialog.vue'

const auth = useAuthStore()
const equipmentList = ref([])
const userList = ref([])
const errorMsg = ref('')
const lendTarget = ref(null)
const returnTarget = ref(null)

async function refresh() {
  lendTarget.value = null
  returnTarget.value = null
  errorMsg.value = ''
  try {
    equipmentList.value = await listEquipment(auth.token)
    if (auth.isAdmin) userList.value = await listUsers(auth.token)
  } catch {
    errorMsg.value = 'データの読み込みに失敗しました'
  }
}

async function handleDelete(managementNumber) {
  try {
    await deleteEquipment(auth.token, managementNumber)
    await refresh()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '削除に失敗しました'
  }
}

function openLendModal(eq) { lendTarget.value = eq }
function openReturnDialog(eq) { returnTarget.value = eq }

onMounted(refresh)
</script>
