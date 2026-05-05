<!--
  備品登録・編集フォームコンポーネント。
  要件ID: RQ-FT-MANAGE-EQUIPMENT
  設計ID: DS-VC-EQUIPMENT-FORM-FT-MANAGE-EQUIPMENT
  要件概要: 管理者が備品ID・名称を入力して新規登録または編集できる。備品IDは編集時に変更不可。
  設計概要: route.params.id の有無で登録・編集モードを切り替え、createEquipment または updateEquipment を呼ぶ。
  呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h5">{{ isEdit ? '備品編集' : '備品登録' }}</h1>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500">
      <v-card-text>
        <v-text-field
          v-model="form.equipment_id"
          label="備品ID"
          :disabled="isEdit"
          data-testid="equipment-id-input"
        />
        <v-text-field
          v-model="form.name"
          label="備品名"
          data-testid="equipment-name-input"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" :loading="loading" data-testid="submit-button" @click="handleSubmit">
          {{ isEdit ? '更新' : '登録' }}
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/equipment')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 備品登録・編集フォームのロジック。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-VC-EQUIPMENT-FORM-FT-MANAGE-EQUIPMENT
 * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createEquipment, updateEquipment, listEquipment } from '../api/equipment.js'

const router = useRouter()
const route = useRoute()
const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const errorMessage = ref('')
const form = ref({ equipment_id: '', name: '' })

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await listEquipment()
      const item = res.data.find((e) => e.equipment_id === route.params.id)
      if (item) {
        form.value.equipment_id = item.equipment_id
        form.value.name = item.name
      }
    } catch {
      errorMessage.value = '備品情報の取得に失敗しました'
    }
  }
})

/**
 * 登録・更新ボタン押下時の処理。バリデーション後にAPIを呼び出し、成功時に備品一覧へ遷移する。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-VC-EQUIPMENT-FORM-FT-MANAGE-EQUIPMENT
 */
async function handleSubmit() {
  errorMessage.value = ''
  if (!form.value.equipment_id || !form.value.name) {
    errorMessage.value = '全ての項目を入力してください'
    return
  }
  loading.value = true
  try {
    if (isEdit.value) {
      await updateEquipment(route.params.id, { name: form.value.name })
    } else {
      await createEquipment({ equipment_id: form.value.equipment_id, name: form.value.name })
    }
    router.push('/admin/equipment')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '操作に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
