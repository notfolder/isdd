<!--
  備品削除確認画面コンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT
  設計ID: DS-VC-EQUIPMENT-DELETE-FT-MANAGE-EQUIPMENT
  要件概要: 管理者が備品の削除前に確認し、削除を実行できる。貸出中備品は削除不可（APIがエラーを返す）。
  設計概要: 備品情報を表示して確認を促し、deleteEquipment を呼び出す。エラーメッセージを表示する。
  呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">備品削除確認</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500" v-if="equipment">
      <v-card-text>
        <p>以下の備品を削除しますか？</p>
        <p><strong>備品ID:</strong> {{ equipment.equipment_id }}</p>
        <p><strong>備品名:</strong> {{ equipment.name }}</p>
        <p><strong>状態:</strong> {{ equipment.status === 'loaned' ? '貸出中' : '貸出可能' }}</p>
      </v-card-text>
      <v-card-actions>
        <v-btn color="error" :loading="loading" data-testid="confirm-delete-button" @click="handleDelete">
          削除する
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/equipment')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 備品削除確認画面のロジック。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-VC-EQUIPMENT-DELETE-FT-MANAGE-EQUIPMENT
 * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listEquipment, deleteEquipment } from '../api/equipment.js'

const router = useRouter()
const route = useRoute()
const equipment = ref(null)
const loading = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  try {
    const res = await listEquipment()
    equipment.value = res.data.find((e) => e.equipment_id === route.params.id)
  } catch {
    errorMessage.value = '備品情報の取得に失敗しました'
  }
})

/**
 * 削除実行処理。APIを呼び出し、成功時に備品一覧へ遷移する。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-VC-EQUIPMENT-DELETE-FT-MANAGE-EQUIPMENT
 */
async function handleDelete() {
  errorMessage.value = ''
  loading.value = true
  try {
    await deleteEquipment(route.params.id)
    router.push('/admin/equipment')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '削除に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
