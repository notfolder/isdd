<!--
  Appコンポーネント - アプリケーションのルートコンポーネント
  
  要件トレーサビリティ:
    要件ID: RQ-AT-WEB-GUI, RQ-FT-LOGIN, RQ-FT-LOGOUT
    設計ID: DS-CL-APP-VUE-UI-LOGIN-SCREEN
    要件概要: アプリケーション全体のレイアウトとナビゲーションを提供する
    設計概要: v-app レイアウトを使用し、ログイン状態に応じてナビゲーションバーを表示する
    呼び出し先: DS-CL-NAVIGATION-BAR-FT-LOGOUT, DS-CL-ROUTER-FT-LOGIN
    呼び出し元: main.js
-->

<template>
  <v-app>
    <!-- ナビゲーションバー（ログイン後のみ表示） -->
    <!-- 要件ID: RQ-FT-LOGOUT -->
    <!-- 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT -->
    <NavigationBar v-if="isLoggedIn" />
    
    <!-- メインコンテンツ -->
    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
/**
 * Appコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-LOGIN, RQ-FT-LOGOUT
 * 設計ID: DS-CL-APP-VUE-UI-LOGIN-SCREEN
 * 要件概要: ログイン状態を管理し、ナビゲーションバーの表示を制御する
 * 設計概要: localStorageからトークンを取得し、ログイン状態を判定する
 */

import NavigationBar from './components/NavigationBar.vue'

export default {
  name: 'App',
  components: {
    NavigationBar
  },
  computed: {
    /**
     * ログイン状態を返す
     * 
     * 要件ID: RQ-FT-LOGIN
     * 設計ID: DS-CL-APP-VUE-UI-LOGIN-SCREEN
     * 要件概要: ログイン状態を判定する
     * 設計概要: localStorageにaccess_tokenが存在するかチェックする
     */
    isLoggedIn() {
      return !!localStorage.getItem('access_token')
    }
  }
}
</script>

<style scoped>
/* スタイルは必要に応じて追加 */
</style>
