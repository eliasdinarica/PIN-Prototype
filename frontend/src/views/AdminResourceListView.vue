<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon, ArrowLeftIcon } from '@heroicons/vue/24/outline'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const router = useRouter()
const resources = ref([])
const categories = ref([])
const loading = ref(true)
const search = ref('')
const categoryFilter = ref('')

const categoryMap = computed(() => Object.fromEntries(categories.value.map(c => [c.id, c.name])))

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return resources.value.filter(r => {
    if (categoryFilter.value && String(r.category) !== String(categoryFilter.value)) return false
    if (q && !r.name.toLowerCase().includes(q)) return false
    return true
  })
})

async function loadAll() {
  loading.value = true
  try {
    const [resRes, catRes] = await Promise.all([
      fetch(`${API}/api/resources/`),
      fetch(`${API}/api/categories-brief/`),
    ])
    resources.value = await resRes.json()
    categories.value = await catRes.json()
  } finally {
    loading.value = false
  }
}

async function remove(resource) {
  if (!confirm(`Delete "${resource.name}"? This cannot be undone.`)) return
  await fetch(`${API}/api/resources/${resource.id}/`, { method: 'DELETE' })
  resources.value = resources.value.filter(r => r.id !== resource.id)
}

onMounted(loadAll)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">
    <div class="max-w-5xl mx-auto px-5 py-8">

      <div class="flex items-center gap-3 mb-6">
        <button
          class="w-9 h-9 rounded-xl bg-surface-500 hover:bg-surface-400 text-white flex items-center justify-center cursor-pointer border-none"
          @click="router.push('/categories')"
        >
          <ArrowLeftIcon class="w-4 h-4" />
        </button>
        <h1 class="text-2xl font-bold text-surface-800 flex-1">Resources admin</h1>
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm cursor-pointer border-none"
          @click="router.push('/admin/resources/new')"
        >
          <PlusIcon class="w-4 h-4" />
          New
        </button>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 mb-6">
        <div class="flex-1 relative">
          <MagnifyingGlassIcon class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
          <input
            v-model="search"
            type="text"
            placeholder="Search by name…"
            class="w-full pl-9 pr-4 py-2.5 rounded-xl bg-white border border-surface-300 text-sm focus:outline-none focus:border-brand-500"
          />
        </div>
        <select
          v-model="categoryFilter"
          class="px-4 py-2.5 rounded-xl bg-white border border-surface-300 text-sm focus:outline-none focus:border-brand-500 cursor-pointer"
        >
          <option value="">All categories</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </div>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
      </div>

      <div v-else-if="filtered.length === 0" class="bg-white rounded-2xl p-12 text-center text-surface-500">
        No resources match your filters.
      </div>

      <div v-else class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div
          v-for="(r, i) in filtered"
          :key="r.id"
          class="flex items-center gap-3 px-4 py-3 hover:bg-surface-100 transition-colors"
          :class="i > 0 && 'border-t border-surface-200'"
        >
          <div class="flex-1 min-w-0">
            <p class="font-medium text-surface-800 truncate">{{ r.name }}</p>
            <p class="text-xs text-surface-500 mt-0.5">{{ categoryMap[r.category] || '—' }}</p>
          </div>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-200 text-surface-600 cursor-pointer bg-transparent border-none"
            @click="router.push(`/admin/resources/${r.id}/edit`)"
          >
            <PencilIcon class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 text-red-500 cursor-pointer bg-transparent border-none"
            @click="remove(r)"
          >
            <TrashIcon class="w-4 h-4" />
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
