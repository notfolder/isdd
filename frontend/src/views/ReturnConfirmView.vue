<!--
  返却確認画面コンポーネント。
  要件ID: RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-VC-RETURN-CONFIRM-FT-RETURN-EQUIPMENT
  要件概要: 管理者が貸出中備品の返却前に確認し、返却を実行できる。
  設計概要: 備品と貸出情報を表示して確認を促し、returnEquipment を呼び出す。
  呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">返却確認</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500" v-if="equipment">
      <v-card-text>
        <p>以下の備品を返却しますか？</p>
        <p><strong>備品ID:</strong> {{ equipment.equipment_id }}</p>
        <p><strong>備品名:</strong> {{ equipment.name }}</p>
        <p><strong>貸出先:</strong> {{ equipment.loan_info?.user_display_name }}</p>
        <p><strong>貸出日:</strong> {{ equipment.loan_info?.loan_date }}</p>
      </v-card-text>
      <v-card-actions>
        <v-btn color="warning" :loading="loading" data-testid="confirm-return-button" @click="handleReturn">
          返却する
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/equipment')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 返却確認画面のロジック。
 * 要件ID: RQ-FT-RETURN-EQUIPMENT
 * 設計ID: DS-VC-RETURN-CONFIRM-FT-RETURN-EQUIPMENT
 * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listEquipment, returnEquipment } from '../api/equipment.js'

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
 * 返却実行処理。APIを呼び出し、成功時に備品一覧へ遷移する。
 * 要件ID: RQ-FT-RETURN-EQUIPMENT
 * 設計ID: DS-VC-RETURN-CONFIRM-FT-RETURN-EQUIPMENT
 */
async function handleReturn() {
  errorMessage.value = ''
  loading.value = true
  try {
    await returnEquipment(route.params.id)
    router.push('/admin/equipment')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '返却に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
