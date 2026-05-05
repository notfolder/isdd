/**
 * 備品状態管理ストア。
 * 備品一覧のフェッチと状態保持を提供する。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT
 * 要件概要: 備品一覧を取得してメモリ内で管理し、各画面コンポーネントに提供する。
 * 設計概要: Pinia defineStore で equipmentList を ref で保持し、fetchEquipment() でAPIから取得する。
 * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-VC-ADMIN-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT, DS-VC-GENERAL-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listEquipment } from '../api/equipment.js'

export const useEquipmentStore = defineStore('equipment', () => {
  const equipmentList = ref([])
  const loading = ref(false)
  const errorMessage = ref('')

  /**
   * バックエンドから全備品一覧を取得してストアに保存する。
   * @returns {Promise<void>}
   * 要件ID: RQ-FT-MANAGE-EQUIPMENT
   * 設計ID: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT
   * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
   * 呼び出し元: DS-VC-ADMIN-EQUIPMENT-LIST-FT-MANAGE-EQUIPMENT
   */
  async function fetchEquipment() {
    loading.value = true
    errorMessage.value = ''
    try {
      const res = await listEquipment()
      equipmentList.value = res.data
    } catch (err) {
      errorMessage.value = err.response?.data?.detail || '備品の取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  return { equipmentList, loading, errorMessage, fetchEquipment }
})
