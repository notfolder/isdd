<!--
  ItemListView - 備品一覧画面
  
  要件トレーサビリティ:
    要件ID: RQ-FT-VIEW-ITEM-LIST
    設計ID: DS-CL-ITEM-LIST-VIEW-FT-VIEW-ITEM-LIST
    要件概要: 備品一覧と貸出状況を表示する
    設計概要: 備品一覧APIを呼び出し、データテーブルで表示する
    呼び出し先: DS-CL-API-CLIENT-FT-LOGIN
    呼び出し元: DS-CL-ROUTER-FT-LOGIN
-->

<template>
  <v-container>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-package-variant</v-icon>
        <span class="text-h5">備品一覧</span>
        <v-spacer />
        <!-- 管理者のみ備品管理画面へのボタンを表示 -->
        <!-- 要件ID: RQ-NF-ACCESS-CONTROL -->
        <!-- 設計ID: DS-UI-ITEM-LIST-SCREEN-FT-VIEW-ITEM-LIST -->
        <v-btn
          v-if="isAdmin"
          color="primary"
          prepend-icon="mdi-cog"
          @click="$router.push('/items/manage')"
        >
          備品管理
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        <!-- 検索フィールド -->
        <v-text-field
          v-model="search"
          label="検索"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          clearable
          hide-details
          class="mb-4"
        />
        
        <!-- 備品一覧テーブル -->
        <!-- 要件ID: RQ-FT-VIEW-ITEM-LIST -->
        <!-- 設計ID: DS-UI-ITEM-LIST-SCREEN-FT-VIEW-ITEM-LIST -->
        <v-data-table
          :headers="headers"
          :items="items"
          :search="search"
          :loading="loading"
          loading-text="読み込み中..."
          no-data-text="データがありません"
          items-per-page-text="表示件数"
          :items-per-page="10"
        >
          <!-- ステータス列のカスタマイズ -->
          <template v-slot:item.status="{ item }">
            <v-chip
              :color="item.status === '利用可能' ? 'success' : 'warning'"
              size="small"
            >
              {{ item.status }}
            </v-chip>
          </template>
          
          <!-- 借り主列のカスタマイズ -->
          <template v-slot:item.borrower="{ item }">
            {{ item.borrower || '-' }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
/**
 * ItemListViewコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-VIEW-ITEM-LIST
 * 設計ID: DS-CL-ITEM-LIST-VIEW-FT-VIEW-ITEM-LIST
 * 要件概要: 備品一覧と貸出状況を表示する
 * 設計概要: 備品一覧APIを呼び出し、データテーブルで表示する
 */

import { itemApi } from '../services/api'

export default {
  name: 'ItemListView',
  data() {
    return {
      items: [],
      search: '',
      loading: false,
      headers: [
        { title: '資産管理番号', key: 'asset_number', align: 'start' },
        { title: '備品名称', key: 'name', align: 'start' },
        { title: 'ステータス', key: 'status', align: 'center' },
        { title: '借り主', key: 'borrower', align: 'start' }
      ]
    }
  },
  computed: {
    /**
     * 管理者権限チェック
     * 
     * 要件ID: RQ-NF-ACCESS-CONTROL
     * 設計ID: DS-CL-ITEM-LIST-VIEW-FT-VIEW-ITEM-LIST
     */
    isAdmin() {
      return localStorage.getItem('user_role') === '管理者'
    }
  },
  mounted() {
    this.loadItems()
  },
  methods: {
    /**
     * 備品一覧を取得
     * 
     * 要件ID: RQ-FT-VIEW-ITEM-LIST
     * 設計ID: DS-CL-ITEM-LIST-VIEW-FT-VIEW-ITEM-LIST
     * 要件概要: 備品一覧APIを呼び出してデータを取得する
     * 設計概要: itemApi.getAll()を呼び出し、取得したデータをitemsに格納する
     */
    async loadItems() {
      this.loading = true
      try {
        const response = await itemApi.getAll()
        this.items = response.data
      } catch (error) {
        console.error('備品一覧の取得に失敗しました', error)
        alert('備品一覧の取得に失敗しました')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
/* スタイルは必要に応じて追加 */
</style>
