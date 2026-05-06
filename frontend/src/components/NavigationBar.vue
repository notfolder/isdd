<!--
  NavigationBar - ナビゲーションバーコンポーネント
  
  要件トレーサビリティ:
    要件ID: RQ-FT-LOGOUT, RQ-NF-ACCESS-CONTROL
    設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
    要件概要: ログアウト機能とナビゲーションメニューを提供する
    設計概要: v-app-bar で画面上部にナビゲーションメニューとログアウトボタンを表示する
    呼び出し先: DS-CL-ROUTER-FT-LOGIN
    呼び出し元: DS-CL-APP-VUE-UI-LOGIN-SCREEN
-->

<template>
  <v-app-bar color="primary" prominent>
    <v-app-bar-title>
      <v-icon class="mr-2">mdi-package-variant-closed</v-icon>
      備品管理・貸出管理システム
    </v-app-bar-title>
    
    <v-spacer />
    
    <!-- ナビゲーションメニュー -->
    <!-- 要件ID: RQ-NF-ACCESS-CONTROL -->
    <!-- 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT -->
    <v-btn
      @click="$router.push('/items')"
      :variant="$route.path === '/items' ? 'flat' : 'text'"
    >
      <v-icon class="mr-1">mdi-package-variant</v-icon>
      備品一覧
    </v-btn>
    
    <!-- 管理者のみ表示 -->
    <v-btn
      v-if="isAdmin"
      @click="$router.push('/items/manage')"
      :variant="$route.path === '/items/manage' ? 'flat' : 'text'"
    >
      <v-icon class="mr-1">mdi-cog</v-icon>
      備品管理
    </v-btn>
    
    <v-btn
      v-if="isAdmin"
      @click="$router.push('/users')"
      :variant="$route.path === '/users' ? 'flat' : 'text'"
    >
      <v-icon class="mr-1">mdi-account-multiple</v-icon>
      利用者管理
    </v-btn>
    
    <v-divider vertical class="mx-4" />
    
    <!-- ユーザー情報 -->
    <v-chip class="mr-4">
      <v-icon class="mr-1">mdi-account</v-icon>
      {{ userName }} ({{ userRole }})
    </v-chip>
    
    <!-- ログアウトボタン -->
    <!-- 要件ID: RQ-FT-LOGOUT -->
    <!-- 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT -->
    <v-btn
      @click="handleLogout"
      prepend-icon="mdi-logout"
    >
      ログアウト
    </v-btn>
  </v-app-bar>
</template>

<script>
/**
 * NavigationBarコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-LOGOUT, RQ-NF-ACCESS-CONTROL
 * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
 * 要件概要: ログアウト機能とナビゲーションメニューを提供する
 * 設計概要: ログアウトボタンをクリックするとlocalStorageをクリアし、ログイン画面にリダイレクトする
 */

export default {
  name: 'NavigationBar',
  computed: {
    /**
     * ユーザーID
     * 
     * 要件ID: RQ-FT-LOGIN
     * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
     */
    userName() {
      return localStorage.getItem('user_id') || ''
    },
    
    /**
     * ユーザー権限
     * 
     * 要件ID: RQ-NF-ACCESS-CONTROL
     * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
     */
    userRole() {
      return localStorage.getItem('user_role') || ''
    },
    
    /**
     * 管理者権限チェック
     * 
     * 要件ID: RQ-NF-ACCESS-CONTROL
     * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
     */
    isAdmin() {
      return this.userRole === '管理者'
    }
  },
  methods: {
    /**
     * ログアウト処理
     * 
     * 要件ID: RQ-FT-LOGOUT
     * 設計ID: DS-CL-NAVIGATION-BAR-FT-LOGOUT
     * 要件概要: ログアウトしてログイン画面に戻る
     * 設計概要: localStorageからトークンとユーザー情報を削除し、ログイン画面にリダイレクトする
     */
    handleLogout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_role')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
/* スタイルは必要に応じて追加 */
</style>
