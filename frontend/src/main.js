/**
 * フロントエンドアプリケーションエントリーポイント。
 * Vue アプリを初期化し、Pinia・Vue Router・Vuetify を登録してマウントする。
 * 要件ID: RQ-FT-LOGIN, RQ-NF-ROLE-ACCESS
 * 設計ID: DS-MD-FRONTEND-FT-MANAGE-EQUIPMENT
 * 要件概要: フロントエンドSPAとして全画面・状態管理・ルーティング・UIコンポーネントを提供する。
 * 設計概要: createApp に Pinia（状態管理）・Vue Router（ルーティング）・Vuetify（UI）を use() で登録する。
 * 呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN, DS-SC-ROUTER-NF-ROLE-ACCESS
 * 呼び出し元: ブラウザ（index.html）
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import App from './App.vue'
import router from './router/index.js'

const vuetify = createVuetify({ components, directives })
const pinia = createPinia()

createApp(App).use(pinia).use(router).use(vuetify).mount('#app')
