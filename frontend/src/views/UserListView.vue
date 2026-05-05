<!--
  利用者管理一覧画面コンポーネント。
  要件ID: RQ-FT-MANAGE-BORROWER
  設計ID: DS-VC-USER-LIST-FT-MANAGE-BORROWER
  要件概要: 管理者が全利用者を一覧確認し、登録・編集・削除操作を開始できる。
  設計概要: UserStore から利用者一覧を取得してテーブル表示し、各行に編集・削除ボタンを表示する。
  呼び出し先: DS-SC-USER-STORE-FT-MANAGE-BORROWER, DS-SC-AUTH-STORE-FT-LOGIN
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h5">利用者管理</h1>
      </v-col>
      <v-col class="text-right">
        <v-btn color="primary" class="mr-2" data-testid="add-user-button" @click="router.push('/admin/users/new')">
          利用者登録
        </v-btn>
        <v-btn class="mr-2" data-testid="back-to-equipment-button" @click="router.push('/admin/equipment')">備品一覧へ戻る</v-btn>
        <v-btn data-testid="logout-button" @click="handleLogout">ログアウト</v-btn>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-table data-testid="user-table">
      <thead>
        <tr>
          <th>ログインID</th>
          <th>利用者名</th>
          <th>権限</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in userStore.userList" :key="user.login_id" :data-testid="`user-row-${user.login_id}`">
          <td>{{ user.login_id }}</td>
          <td>{{ user.display_name }}</td>
          <td>{{ user.role === 'admin' ? '管理者' : '一般利用者' }}</td>
          <td>
            <v-btn
              size="small"
              color="secondary"
              class="mr-1"
              :data-testid="`edit-user-button-${user.login_id}`"
              @click="router.push(`/admin/users/${user.login_id}/edit`)"
            >
              編集
            </v-btn>
            <v-btn
              size="small"
              color="error"
              :data-testid="`delete-user-button-${user.login_id}`"
              @click="router.push(`/admin/users/${user.login_id}/delete`)"
            >
              削除
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup>
/**
 * 利用者管理一覧画面のロジック。
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-VC-USER-LIST-FT-MANAGE-BORROWER
 * 呼び出し先: DS-SC-USER-STORE-FT-MANAGE-BORROWER
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useUserStore } from '../stores/user.js'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const errorMessage = ref('')

onMounted(async () => {
  await userStore.fetchUsers()
  errorMessage.value = userStore.errorMessage
})

/**
 * ログアウト処理。AuthStore のセッションをクリアしてログイン画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-VC-USER-LIST-FT-MANAGE-BORROWER
 */
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
