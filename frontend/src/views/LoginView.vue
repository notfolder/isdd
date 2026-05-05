<!--
  ログイン画面コンポーネント。
  要件ID: RQ-FT-LOGIN
  設計ID: DS-VC-LOGIN-FT-LOGIN
  要件概要: ログインIDとパスワードを入力して認証し、ロールに応じた画面へ遷移する。
  設計概要: AuthStore.login() を呼び出し、成功時は管理者→/admin/equipment、一般利用者→/general/equipment へ Vue Router で遷移する。
  呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="6" md="4">
        <v-card>
          <v-card-title class="text-h5 text-center pa-4">備品管理システム</v-card-title>
          <v-card-text>
            <v-alert v-if="authStore.errorMessage" type="error" class="mb-4" data-testid="error-message">
              {{ authStore.errorMessage }}
            </v-alert>
            <v-text-field
              v-model="loginId"
              label="ログインID"
              data-testid="login-id"
              @keyup.enter="handleLogin"
            />
            <v-text-field
              v-model="password"
              label="パスワード"
              type="password"
              data-testid="password"
              @keyup.enter="handleLogin"
            />
          </v-card-text>
          <v-card-actions class="pa-4">
            <v-btn
              color="primary"
              block
              :loading="loading"
              data-testid="login-button"
              @click="handleLogin"
            >
              ログイン
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
/**
 * ログイン画面のロジック。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-VC-LOGIN-FT-LOGIN
 * 呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
const router = useRouter()
const loginId = ref('')
const password = ref('')
const loading = ref(false)

/**
 * ログインボタン押下時の処理。認証後にロールに応じた画面へ遷移する。
 * 要件ID: RQ-FT-LOGIN, RQ-NF-ROLE-ACCESS
 * 設計ID: DS-VC-LOGIN-FT-LOGIN
 */
async function handleLogin() {
  if (!loginId.value || !password.value) return
  loading.value = true
  const role = await authStore.login(loginId.value, password.value)
  loading.value = false
  if (role === 'admin') {
    router.push('/admin/equipment')
  } else if (role === 'general') {
    router.push('/general/equipment')
  }
}
</script>
