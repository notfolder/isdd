/**
 * Vite設定ファイル
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-AT-WEB-GUI
 *   設計ID: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
 *   要件概要: Vue 3 + Vuetify 3でWebアプリケーションを構築する
 *   設計概要: Viteのビルド設定とVuetifyプラグインを設定する
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true })
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 5173
    }
  }
})
