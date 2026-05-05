<!--
  アプリケーションルートコンポーネント。
  router-view でページ遷移を管理し、自動ログアウトタイマーを制御する。
  要件ID: RQ-NF-SESSION-AUTO-LOGOUT-60MIN
  設計ID: DS-VC-APP-NF-SESSION-AUTO-LOGOUT
  要件概要: ログインから60分経過した場合に自動でログアウトしてログインページへ遷移する。
  設計概要: setInterval で60秒ごとに isSessionExpired() を確認し、期限切れ時に window.location.href で強制リダイレクトする。
  呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN
  呼び出し元: DS-MD-FRONTEND-FT-MANAGE-EQUIPMENT
-->
<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

const authStore = useAuthStore()
const router = useRouter()

let sessionTimer = null

onMounted(() => {
  sessionTimer = setInterval(() => {
    if (authStore.isSessionExpired()) {
      authStore.logout()
      // window.location.href を使用する（router.push は非同期のため page.clock.fastForward と相性が悪い）
      window.location.href = '/login'
    }
  }, 60 * 1000)
})

onUnmounted(() => {
  if (sessionTimer) clearInterval(sessionTimer)
})
</script>
