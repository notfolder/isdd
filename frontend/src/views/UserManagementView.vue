<!--
  UserManagementView - 利用者管理画面
  
  要件トレーサビリティ:
    要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
    設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
    要件概要: 利用者の登録、編集、削除、一覧表示を行う（管理者のみ）
    設計概要: 利用者一覧を表示し、各操作用のダイアログを提供する
    呼び出し先: DS-CL-API-CLIENT-FT-LOGIN
    呼び出し元: DS-CL-ROUTER-FT-LOGIN
-->

<template>
  <v-container>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-account-multiple</v-icon>
        <span class="text-h5">利用者管理</span>
        <v-spacer />
        <!-- 新規登録ボタン -->
        <!-- 要件ID: RQ-FT-REGISTER-USER -->
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
        
        <!-- 利用者一覧テーブル -->
        <!-- 要件ID: RQ-FT-VIEW-USER-LIST -->
        <v-data-table
          :headers="headers"
          :items="users"
          :search="search"
          :loading="loading"
          loading-text="読み込み中..."
          no-data-text="データがありません"
          items-per-page-text="表示件数"
          :items-per-page="10"
        >
          <!-- 権限列のカスタマイズ -->
          <template v-slot:item.role="{ item }">
            <v-chip
              :color="item.role === '管理者' ? 'primary' : 'secondary'"
              size="small"
            >
              {{ item.role }}
            </v-chip>
          </template>
          
          <!-- 操作列 -->
          <!-- 要件ID: RQ-FT-EDIT-USER, RQ-FT-DELETE-USER -->
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
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
    
    <!-- 新規登録ダイアログ -->
    <!-- 要件ID: RQ-FT-REGISTER-USER -->
    <v-dialog v-model="createDialog" max-width="500px">
      <v-card>
        <v-card-title>利用者の新規登録</v-card-title>
        <v-card-text>
          <v-form ref="createForm">
            <v-text-field
              v-model="newUser.user_id"
              label="ユーザーID"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
            <v-text-field
              v-model="newUser.name"
              label="氏名"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
            <v-text-field
              v-model="newUser.password"
              label="パスワード"
              type="password"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
            <v-select
              v-model="newUser.role"
              label="権限"
              :items="roleOptions"
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
    <!-- 要件ID: RQ-FT-EDIT-USER -->
    <v-dialog v-model="editDialog" max-width="500px">
      <v-card>
        <v-card-title>利用者の編集</v-card-title>
        <v-card-text>
          <v-form ref="editForm">
            <v-text-field
              v-model="editUser.user_id"
              label="ユーザーID"
              variant="outlined"
              readonly
              disabled
            />
            <v-text-field
              v-model="editUser.name"
              label="氏名"
              variant="outlined"
              :rules="[rules.required]"
              required
            />
            <v-text-field
              v-model="editUser.password"
              label="パスワード（変更する場合のみ入力）"
              type="password"
              variant="outlined"
              hint="空欄の場合は変更されません"
              persistent-hint
            />
            <v-select
              v-model="editUser.role"
              label="権限"
              :items="roleOptions"
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
    <!-- 要件ID: RQ-FT-DELETE-USER -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>利用者の削除</v-card-title>
        <v-card-text>
          利用者「{{ deleteUser.name }}」を削除してもよろしいですか？
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="deleteDialog = false">キャンセル</v-btn>
          <v-btn color="error" @click="handleDelete" :loading="actionLoading">削除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
/**
 * UserManagementViewコンポーネントのスクリプト
 * 
 * 要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
 * 設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
 */

import { userApi } from '../services/api'

export default {
  name: 'UserManagementView',
  data() {
    return {
      users: [],
      search: '',
      loading: false,
      actionLoading: false,
      headers: [
        { title: 'ユーザーID', key: 'user_id', align: 'start' },
        { title: '氏名', key: 'name', align: 'start' },
        { title: '権限', key: 'role', align: 'center' },
        { title: '操作', key: 'actions', align: 'center', sortable: false }
      ],
      createDialog: false,
      editDialog: false,
      deleteDialog: false,
      newUser: {
        user_id: '',
        name: '',
        password: '',
        role: '一般利用者'
      },
      editUser: {},
      deleteUser: {},
      roleOptions: ['管理者', '一般利用者'],
      rules: {
        required: value => !!value || '必須項目です'
      }
    }
  },
  mounted() {
    this.loadUsers()
  },
  methods: {
    /**
     * 利用者一覧を取得
     * 
     * 要件ID: RQ-FT-VIEW-USER-LIST
     * 設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
     */
    async loadUsers() {
      this.loading = true
      try {
        const response = await userApi.getAll()
        this.users = response.data
      } catch (error) {
        console.error('利用者一覧の取得に失敗しました', error)
        alert('利用者一覧の取得に失敗しました')
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 新規登録ダイアログを開く
     * 
     * 要件ID: RQ-FT-REGISTER-USER
     * 設計ID: DS-UI-USER-MANAGEMENT-SCREEN-FT-REGISTER-USER
     */
    openCreateDialog() {
      this.newUser = { user_id: '', name: '', password: '', role: '一般利用者' }
      this.createDialog = true
    },
    
    /**
     * 利用者を新規登録
     * 
     * 要件ID: RQ-FT-REGISTER-USER
     * 設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
     */
    async handleCreate() {
      if (!this.newUser.user_id || !this.newUser.name || !this.newUser.password || !this.newUser.role) {
        alert('すべての項目を入力してください')
        return
      }
      
      this.actionLoading = true
      try {
        await userApi.create(
          this.newUser.user_id,
          this.newUser.name,
          this.newUser.password,
          this.newUser.role
        )
        this.createDialog = false
        await this.loadUsers()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('利用者の登録に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 編集ダイアログを開く
     * 
     * 要件ID: RQ-FT-EDIT-USER
     * 設計ID: DS-UI-USER-MANAGEMENT-SCREEN-FT-EDIT-USER
     */
    openEditDialog(user) {
      this.editUser = { ...user, password: '' }
      this.editDialog = true
    },
    
    /**
     * 利用者を編集
     * 
     * 要件ID: RQ-FT-EDIT-USER
     * 設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
     */
    async handleEdit() {
      if (!this.editUser.name || !this.editUser.role) {
        alert('氏名と権限を入力してください')
        return
      }
      
      this.actionLoading = true
      try {
        await userApi.update(
          this.editUser.user_id,
          this.editUser.name,
          this.editUser.password || null,
          this.editUser.role
        )
        this.editDialog = false
        await this.loadUsers()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('利用者の更新に失敗しました')
        }
      } finally {
        this.actionLoading = false
      }
    },
    
    /**
     * 削除確認ダイアログを開く
     * 
     * 要件ID: RQ-FT-DELETE-USER
     * 設計ID: DS-UI-USER-MANAGEMENT-SCREEN-FT-DELETE-USER
     */
    openDeleteDialog(user) {
      this.deleteUser = { ...user }
      this.deleteDialog = true
    },
    
    /**
     * 利用者を削除
     * 
     * 要件ID: RQ-FT-DELETE-USER
     * 設計ID: DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
     */
    async handleDelete() {
      this.actionLoading = true
      try {
        await userApi.delete(this.deleteUser.user_id)
        this.deleteDialog = false
        await this.loadUsers()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('利用者の削除に失敗しました')
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
