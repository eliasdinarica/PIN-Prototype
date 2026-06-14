import { ref, watch } from 'vue'

const KEY = 'savedResources'

function load() {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] }
}

// Shared reactive list of saved resource IDs (persisted to localStorage).
const savedIds = ref(load())

watch(savedIds, (v) => {
  localStorage.setItem(KEY, JSON.stringify(v))
}, { deep: true })

export function useSaved() {
  const isSaved = (id) => savedIds.value.includes(id)
  const toggleSave = (id) => {
    savedIds.value = isSaved(id)
      ? savedIds.value.filter((x) => x !== id)
      : [...savedIds.value, id]
  }
  return { savedIds, isSaved, toggleSave }
}
