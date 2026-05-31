<!--
  ユーザー管理画面コンポーネント。
  要件ID: RQ-UI-USER-LIST-SCREEN / 設計ID: DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN
  要件概要: 管理者が社員アカウントの一覧確認・追加・削除を行う。
  設計概要: UserListView。貸出中ユーザーの削除試行時にエラーを表示する。
-->
<template>
  <v-container>
    <v-row class="mb-3" align="center">
      <v-col><span class="text-h6">ユーザー管理</span></v-col>
      <v-col cols="auto">
        <v-btn color="primary" to="/users/new">+ 新規追加</v-btn>
        <v-btn variant="text" to="/equipment" class="ml-2">← 備品一覧</v-btn>
      </v-col>
    </v-row>
    <v-alert v-if="errorMsg" type="error" class="mb-3">{{ errorMsg }}</v-alert>
    <v-table>
      <thead>
        <tr><th>氏名</th><th>メールアドレス</th><th>権限</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="user in userList" :key="user.id">
          <td>{{ user.name }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.role === 'admin' ? '管理者' : '一般' }}</td>
          <td>
            <v-btn size="small" color="primary" class="mr-1" :to="`/users/${user.id}/edit`">編集</v-btn>
            <v-btn size="small" color="error" @click="handleDelete(user.id)">削除</v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { listUsers, deleteUser } from '../api/users.js'

const auth = useAuthStore()
const userList = ref([])
const errorMsg = ref('')

async function refresh() {
  errorMsg.value = ''
  try { userList.value = await listUsers(auth.token) }
  catch { errorMsg.value = 'データの読み込みに失敗しました' }
}

async function handleDelete(userId) {
  try { await deleteUser(auth.token, userId); await refresh() }
  catch (err) { errorMsg.value = err.response?.data?.detail || '削除に失敗しました' }
}

onMounted(refresh)
</script>
