<!--
  LoginView - ログイン画面
  
  要件トレーサビリティ:
    要件ID: RQ-FT-LOGIN
    設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
    要件概要: ユーザーIDとパスワードを入力してログインする
    設計概要: ログインフォームを表示し、認証APIを呼び出してJWTトークンを取得する
    呼び出し先: DS-CL-API-CLIENT-FT-LOGIN
    呼び出し元: DS-CL-ROUTER-FT-LOGIN
-->

<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-card-title class="text-h5 text-center pa-6">
            備品管理・貸出管理システム
          </v-card-title>
          
          <v-card-text>
            <!-- ログインフォーム -->
            <!-- 要件ID: RQ-FT-LOGIN -->
            <!-- 設計ID: DS-UI-LOGIN-SCREEN-FT-LOGIN -->
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="userId"
                label="ユーザーID"
                prepend-icon="mdi-account"
                variant="outlined"
                :rules="[rules.required]"
                required
              />
              
              <v-text-field
                v-model="password"
                label="パスワード"
                prepend-icon="mdi-lock"
                type="password"
                variant="outlined"
                :rules="[rules.required]"
                required
              />
              
              <!-- エラーメッセージ -->
              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                closable
                @click:close="errorMessage = ''"
                class="mb-4"
              >
                {{ errorMessage }}
              </v-alert>
              
              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="loading"
              >
                ログイン
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
/**
 * LoginViewコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
 * 要件概要: ユーザーIDとパスワードでログインし、JWTトークンを取得する
 * 設計概要: ログインAPIを呼び出し、成功時はトークンをlocalStorageに保存して備品一覧画面に遷移する
 */

import { authApi } from '../services/api'

export default {
  name: 'LoginView',
  data() {
    return {
      userId: '',
      password: '',
      errorMessage: '',
      loading: false,
      rules: {
        required: value => !!value || '必須項目です'
      }
    }
  },
  methods: {
    /**
     * ログイン処理
     * 
     * 要件ID: RQ-FT-LOGIN
     * 設計ID: DS-CL-LOGIN-VIEW-FT-LOGIN
     * 要件概要: ユーザーIDとパスワードでログインする
     * 設計概要: ログインAPIを呼び出し、JWTトークンとユーザー情報をlocalStorageに保存する
     */
    async handleLogin() {
      if (!this.userId || !this.password) {
        this.errorMessage = 'ユーザーIDとパスワードを入力してください'
        return
      }
      
      this.loading = true
      this.errorMessage = ''
      
      try {
        const response = await authApi.login(this.userId, this.password)
        const { access_token, user_id, role } = response.data
        
        // JWTトークンとユーザー情報をlocalStorageに保存
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('user_id', user_id)
        localStorage.setItem('user_role', role)
        
        // 備品一覧画面に遷移
        this.$router.push('/items')
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.errorMessage = 'ユーザーIDまたはパスワードが正しくありません'
        } else {
          this.errorMessage = 'ログインに失敗しました'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
}
</style>
