<!--
  ItemManagementView - 備品管理画面
  
  要件トレーサビリティ:
    要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM
    設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
    要件概要: 備品の登録、編集、削除、貸出、返却を行う（管理者のみ）
    設計概要: 備品一覧を表示し、各操作用のダイアログを提供する
    呼び出し先: DS-CL-API-CLIENT-FT-LOGIN
    呼び出し元: DS-CL-ROUTER-FT-LOGIN
-->

<template>
  <v-container>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-btn
          icon
          @click="$router.push('/items')"
          class="mr-2"
        >
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <v-icon class="mr-2">mdi-cog</v-icon>
        <span class="text-h5">備品管理</span>
        <v-spacer />
        <!-- 新規登録ボタン -->
        <!-- 要件ID: RQ-FT-REGISTER-ITEM -->
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          新規登録
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
          <!-- ステータス列 -->
          <template v-slot:item.status="{ item }">
            <v-chip
              :color="item.status === '利用可能' ? 'success' : 'warning'"
              size="small"
            >
              {{ item.status }}
            </v-chip>
          </template>
          
          <!-- 借り主列 -->
          <template v-slot:item.borrower="{ item }">
            {{ item.borrower || '-' }}
          </template>
          
          <!-- 操作列 -->
          <!-- 要件ID: RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM -->
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="openEditDialog(item)"
              class="mr-1"
            >
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              color="error"
              @click="openDeleteDialog(item)"
              class="mr-1"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
            <v-btn
              v-if="!item.borrower"
              icon
              size="small"
              color="primary"
              @click="openLendDialog(item)"
            >
              <v-icon>mdi-account-arrow-right</v-icon>
            </v-btn>
            <v-btn
              v-else
              icon
              size="small"
              color="success"
              @click="openReturnDialog(item)"
            >
              <v-icon>mdi-account-arrow-left</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
    
    <!-- 新規登録ダイアログ -->
    <!-- 要件ID: RQ-FT-REGISTER-ITEM -->
    <v-dialog v-model="createDialog" max-width="500px">
      <v-card>
        <v-card-title>備品の新規登録</v-card-title>
        <v-card-text>
          <v-form ref="createForm">
            <v-text-field
              v-model="newItem.asset_number"
              label="資産管理番号"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
            <v-text-field
              v-model="newItem.name"
              label="備品名称"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="createDialog = false">キャンセル</v-btn>
          <v-btn color="primary" @click="handleCreate" :loading="actionLoading">登録</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 編集ダイアログ -->
    <!-- 要件ID: RQ-FT-EDIT-ITEM -->
    <v-dialog v-model="editDialog" max-width="500px">
      <v-card>
        <v-card-title>備品の編集</v-card-title>
        <v-card-text>
          <v-form ref="editForm">
            <v-text-field
              v-model="editItem.asset_number"
              label="資産管理番号"
              variant="outlined"
              readonly
              disabled
            />
            <v-text-field
              v-model="editItem.name"
              label="備品名称"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="editDialog = false">キャンセル</v-btn>
          <v-btn color="primary" @click="handleEdit" :loading="actionLoading">更新</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 削除確認ダイアログ -->
    <!-- 要件ID: RQ-FT-DELETE-ITEM -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>備品の削除</v-card-title>
        <v-card-text>
          備品「{{ deleteItem.name }}」を削除してもよろしいですか？
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="deleteDialog = false">キャンセル</v-btn>
          <v-btn color="error" @click="handleDelete" :loading="actionLoading">削除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 貸出ダイアログ -->
    <!-- 要件ID: RQ-FT-LEND-ITEM -->
    <v-dialog v-model="lendDialog" max-width="500px">
      <v-card>
        <v-card-title>備品の貸出</v-card-title>
        <v-card-text>
          <v-form ref="lendForm">
            <v-text-field
              v-model="lendItem.asset_number"
              label="資産管理番号"
              variant="outlined"
              readonly
              disabled
            />
            <v-text-field
              v-model="lendItem.name"
              label="備品名称"
              variant="outlined"
              readonly
              disabled
            />
            <v-text-field
              v-model="lendItem.borrower"
              label="借り主"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="lendDialog = false">キャンセル</v-btn>
          <v-btn color="primary" @click="handleLend" :loading="actionLoading">貸出</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 返却確認ダイアログ -->
    <!-- 要件ID: RQ-FT-RETURN-ITEM -->
    <v-dialog v-model="returnDialog" max-width="400px">
      <v-card>
        <v-card-title>備品の返却</v-card-title>
        <v-card-text>
          備品「{{ returnItem.name }}」を返却してもよろしいですか？<br>
          借り主: {{ returnItem.borrower }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="returnDialog = false">キャンセル</v-btn>
          <v-btn color="success" @click="handleReturn" :loading="actionLoading">返却</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
/**
 * ItemManagementViewコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM
 * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
 */

import { itemApi } from '../services/api'

export default {
  name: 'ItemManagementView',
  data() {
    return {
      items: [],
      search: '',
      loading: false,
      actionLoading: false,
      headers: [
        { title: '資産管理番号', key: 'asset_number', align: 'start' },
        { title: '備品名称', key: 'name', align: 'start' },
        { title: 'ステータス', key: 'status', align: 'center' },
        { title: '借り主', key: 'borrower', align: 'start' },
        { title: '操作', key: 'actions', align: 'center', sortable: false }
      ],
      createDialog: false,
      editDialog: false,
      deleteDialog: false,
      lendDialog: false,
      returnDialog: false,
      newItem: {
        asset_number: '',
        name: ''
      },
      editItem: {},
      deleteItem: {},
      lendItem: {},
      returnItem: {},
      rules: {
        required: value => !!value || '必須項目です'
      }
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
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
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
    },
    
    /**
     * 新規登録ダイアログを開く
     * 
     * 要件ID: RQ-FT-REGISTER-ITEM
     * 設計ID: DS-UI-ITEM-MANAGEMENT-SCREEN-FT-REGISTER-ITEM
     */
    openCreateDialog() {
      this.newItem = { asset_number: '', name: '' }
      this.createDialog = true
    },
    
    /**
     * 備品を新規登録
     * 
     * 要件ID: RQ-FT-REGISTER-ITEM
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
     */
    async handleCreate() {
      if (!this.newItem.asset_number || !this.newItem.name) {
        alert('すべての項目を入力してください')
        return
      }
      
      this.actionLoading = true
      try {
        await itemApi.create(this.newItem.asset_number, this.newItem.name)
        this.createDialog = false
        await this.loadItems()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('備品の登録に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 編集ダイアログを開く
     * 
     * 要件ID: RQ-FT-EDIT-ITEM
     * 設計ID: DS-UI-ITEM-MANAGEMENT-SCREEN-FT-EDIT-ITEM
     */
    openEditDialog(item) {
      this.editItem = { ...item }
      this.editDialog = true
    },
    
    /**
     * 備品を編集
     * 
     * 要件ID: RQ-FT-EDIT-ITEM
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
     */
    async handleEdit() {
      if (!this.editItem.name) {
        alert('備品名称を入力してください')
        return
      }
      
      this.actionLoading = true
      try {
        await itemApi.update(this.editItem.asset_number, this.editItem.name)
        this.editDialog = false
        await this.loadItems()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('備品の更新に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 削除確認ダイアログを開く
     * 
     * 要件ID: RQ-FT-DELETE-ITEM
     * 設計ID: DS-UI-ITEM-MANAGEMENT-SCREEN-FT-DELETE-ITEM
     */
    openDeleteDialog(item) {
      this.deleteItem = { ...item }
      this.deleteDialog = true
    },
    
    /**
     * 備品を削除
     * 
     * 要件ID: RQ-FT-DELETE-ITEM
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
     */
    async handleDelete() {
      this.actionLoading = true
      try {
        await itemApi.delete(this.deleteItem.asset_number)
        this.deleteDialog = false
        await this.loadItems()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('備品の削除に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 貸出ダイアログを開く
     * 
     * 要件ID: RQ-FT-LEND-ITEM
     * 設計ID: DS-UI-ITEM-MANAGEMENT-SCREEN-FT-LEND-ITEM
     */
    openLendDialog(item) {
      this.lendItem = { ...item, borrower: '' }
      this.lendDialog = true
    },
    
    /**
     * 備品を貸出
     * 
     * 要件ID: RQ-FT-LEND-ITEM
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
     */
    async handleLend() {
      if (!this.lendItem.borrower) {
        alert('借り主を入力してください')
        return
      }
      
      this.actionLoading = true
      try {
        await itemApi.lend(this.lendItem.asset_number, this.lendItem.borrower)
        this.lendDialog = false
        await this.loadItems()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('備品の貸出に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 返却確認ダイアログを開く
     * 
     * 要件ID: RQ-FT-RETURN-ITEM
     * 設計ID: DS-UI-ITEM-MANAGEMENT-SCREEN-FT-RETURN-ITEM
     */
    openReturnDialog(item) {
      this.returnItem = { ...item }
      this.returnDialog = true
    },
    
    /**
     * 備品を返却
     * 
     * 要件ID: RQ-FT-RETURN-ITEM
     * 設計ID: DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM
     */
    async handleReturn() {
      this.actionLoading = true
      try {
        await itemApi.return(this.returnItem.asset_number)
        this.returnDialog = false
        await this.loadItems()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('備品の返却に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    }
  }
}
</script>

<style scoped>
/* スタイルは必要に応じて追加 */
</style>
