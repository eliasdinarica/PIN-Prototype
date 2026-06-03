<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MagnifyingGlassIcon, InboxIcon } from '@heroicons/vue/24/outline'
import ResourceList from '@/components/ResourceList.vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const route = useRoute()
const router = useRouter()

const editableQuery = ref(route.query.q || '')
const loading = ref(false)
const reply = ref('')
const resources = ref([])
const error = ref('')

const sections = computed(() =>
  resources.value.length ? [{ key: 'all', items: resources.value }] : []
)

async function fetchResults(q) {
  if (!q?.trim()) return
  loading.value = true
  reply.value = ''
  resources.value = []
  error.value = ''
  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q, history: [] }),
    })
    const data = await res.json()
    if (data.error) {
      error.value = data.error
    } else {
      reply.value = data.reply
      resources.value = data.resources || []
    }
  } catch {
    error.value = 'Connection error. Please try again.'
  }
  loading.value = false
}

function search() {
  const q = editableQuery.value.trim()
  if (!q) return
  router.push(`/ai?q=${encodeURIComponent(q)}`)
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    search()
  }
}

onMounted(() => fetchResults(route.query.q))

watch(() => route.query.q, (newQ) => {
  editableQuery.value = newQ || ''
  fetchResults(newQ)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">
    <div class="max-w-4xl mx-auto px-5 py-8">

      <!-- Query input -->
      <div class="flex items-start gap-3 mb-8">
        <div class="flex-1 flex items-start gap-2 bg-white rounded-2xl shadow-sm border border-surface-200 px-4 py-3">
          <MagnifyingGlassIcon class="w-5 h-5 text-surface-400 mt-0.5 shrink-0" />
          <textarea
            v-model="editableQuery"
            rows="1"
            placeholder="What do you need help with?"
            class="flex-1 resize-none text-surface-800 text-base leading-snug outline-none bg-transparent placeholder-surface-400"
            style="max-height: 120px; overflow-y: auto;"
            @keydown="onKeydown"
          />
        </div>
        <button
          :disabled="!editableQuery.trim() || loading"
          class="h-12 px-5 bg-brand-500 hover:bg-brand-600 disabled:bg-surface-200 text-white rounded-2xl font-medium text-sm transition-colors cursor-pointer border-none shrink-0 flex items-center gap-2"
          @click="search"
        >
          <span>Search</span>
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
      </div>

      <!-- Error -->
      <p v-else-if="error" class="text-red-500 text-sm">{{ error }}</p>

      <!-- Results -->
      <template v-else-if="reply || resources.length">

        <!-- AI reply as description -->
        <p v-if="reply" class="text-gray-500 text-sm mb-8 leading-relaxed">{{ reply }}</p>

        <!-- No resources -->
        <div v-if="!sections.length" class="bg-surface-500 rounded-2xl p-12 text-center shadow-sm">
          <InboxIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-400 text-sm">No resources found for your question.</p>
        </div>

        <ResourceList
          v-else
          :sections="sections"
          show-category
          :feedback-map="{}"
        />

      </template>

    </div>
  </div>
</template>
