<!--
  ログイン画面コンポーネント。
  要件ID: RQ-UI-LOGIN-SCREEN / 設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
  要件概要: メールアドレスとパスワードで認証し備品一覧へ遷移する。
  設計概要: LoginView。認証失敗時はエラーメッセージをフォーム下に表示する。
-->
<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card>
          <v-card-title class="text-center text-h5 pa-4">備品管理システム</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="メールアドレス"
                type="email"
                required
                variant="outlined"
                class="mb-3"
              />
              <v-text-field
                v-model="password"
                label="パスワード"
                type="password"
                required
                variant="outlined"
                class="mb-3"
              />
              <v-alert v-if="errorMsg" type="error" class="mb-3" density="compact">
                {{ errorMsg }}
              </v-alert>
              <v-btn type="submit" color="primary" block :loading="loading">ログイン</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/equipment')
  } catch {
    errorMsg.value = 'メールアドレスまたはパスワードが正しくありません'
  } finally {
    loading.value = false
  }
}
</script>
