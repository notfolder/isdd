/**
 * Vue アプリケーションエントリーポイント
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-AT-WEB-GUI
 *   設計ID: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
 *   要件概要: Vue 3 + Vuetify 3でWebアプリケーションを起動する
 *   設計概要: Vueアプリケーションを作成し、Vuetify、ルーターを登録する
 *   呼び出し先: DS-CL-ROUTER-FT-LOGIN, DS-CL-APP-VUE-UI-LOGIN-SCREEN
 *   呼び出し元: index.html
 */

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Vuetifyの設定
// 要件ID: RQ-AT-WEB-GUI
// 設計ID: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
// 要件概要: Vuetify 3を使用してマテリアルデザインのUIを提供する
// 設計概要: Vuetifyインスタンスを作成し、日本語ロケールとテーマを設定する
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light'
  }
})

// Vueアプリケーションの作成と起動
// 要件ID: RQ-AT-WEB-GUI
// 設計ID: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
// 要件概要: Vueアプリケーションを起動する
// 設計概要: Vuetifyとルーターを登録し、#appにマウントする
const app = createApp(App)
app.use(router)
app.use(vuetify)
app.mount('#app')
