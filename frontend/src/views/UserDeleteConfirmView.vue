<!--
  利用者削除確認画面コンポーネント。
  要件ID: RQ-FT-MANAGE-BORROWER
  設計ID: DS-VC-USER-DELETE-FT-MANAGE-BORROWER
  要件概要: 管理者が利用者の削除前に確認し、削除を実行できる。自己削除・最後の管理者削除・貸出中利用者削除はAPIがエラーを返す。
  設計概要: 利用者情報を表示して確認を促し、deleteUser を呼び出す。エラーメッセージを表示する。
  呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">利用者削除確認</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500" v-if="user">
      <v-card-text>
        <p>以下の利用者を削除しますか？</p>
        <p><strong>ログインID:</strong> {{ user.login_id }}</p>
        <p><strong>利用者名:</strong> {{ user.display_name }}</p>
        <p><strong>権限:</strong> {{ user.role === 'admin' ? '管理者' : '一般利用者' }}</p>
      </v-card-text>
      <v-card-actions>
        <v-btn color="error" :loading="loading" data-testid="confirm-delete-button" @click="handleDelete">
          削除する
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/users')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 利用者削除確認画面のロジック。
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-VC-USER-DELETE-FT-MANAGE-BORROWER
 * 呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listUsers, deleteUser } from '../api/users.js'

const router = useRouter()
const route = useRoute()
const user = ref(null)
const loading = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  try {
    const res = await listUsers()
    user.value = res.data.find((u) => u.login_id === route.params.id)
  } catch {
    errorMessage.value = '利用者情報の取得に失敗しました'
  }
})

/**
 * 削除実行処理。APIを呼び出し、成功時に利用者一覧へ遷移する。
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-VC-USER-DELETE-FT-MANAGE-BORROWER
 */
async function handleDelete() {
  errorMessage.value = ''
  loading.value = true
  try {
    await deleteUser(route.params.id)
    router.push('/admin/users')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '削除に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
