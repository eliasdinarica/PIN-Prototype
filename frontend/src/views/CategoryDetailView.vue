<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ResourceCard from '@/components/ResourceCard.vue'

const route = useRoute()
const router = useRouter()
const category = ref(null)
const loading = ref(true)
const openedResource = ref(null)
const pdfBlobUrl = ref(null)
const pdfLoading = ref(false)

async function openResource(resource) {
  openedResource.value = resource
  pdfLoading.value = true
  pdfBlobUrl.value = null
  try {
    const res = await fetch(resource.file)
    const blob = await res.blob()
    pdfBlobUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    console.error('Failed to load PDF', e)
  } finally {
    pdfLoading.value = false
  }
}

function closeModal() {
  if (pdfBlobUrl.value) URL.revokeObjectURL(pdfBlobUrl.value)
  pdfBlobUrl.value = null
  openedResource.value = null
}

onMounted(async () => {
  try {
    const res = await fetch(`http://localhost:8000/api/categories/${route.params.id}/`)
    category.value = await res.json()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-violet-50 to-violet-100">

    <!-- Sticky top bar -->
    <div class="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-100 px-5 py-3">
      <div class="max-w-lg mx-auto flex items-center gap-3">
        <button
          class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-indigo-50 text-violet-500 hover:text-indigo-600 transition-colors cursor-pointer bg-transparent border-none text-lg"
          @click="router.push('/categories')"
        >
          ←
        </button>
        <template v-if="category">
          <span class="text-xl leading-none">{{ category.emoji }}</span>
          <h1 class="font-bold text-indigo-950 truncate">{{ category.name }}</h1>
        </template>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>

    <div v-else-if="category" class="max-w-lg mx-auto px-5 py-8">

      <p class="text-gray-500 text-sm mb-8 leading-relaxed">{{ category.description }}</p>

      <!-- Empty -->
      <div v-if="category.resources.length === 0" class="bg-white rounded-2xl p-12 text-center shadow-sm">
        <div class="text-4xl mb-3">📭</div>
        <p class="text-gray-400 text-sm">No documents in this category yet.</p>
      </div>

      <!-- Resources -->
      <div v-else class="flex flex-col gap-3">
        <ResourceCard
          v-for="resource in category.resources"
          :key="resource.id"
          :resource="resource"
          @open="openResource"
        />
      </div>

    </div>

    <!-- PDF Modal -->
    <Transition
      enter-from-class="opacity-0"
      enter-active-class="transition-opacity duration-200"
      leave-to-class="opacity-0"
      leave-active-class="transition-opacity duration-200"
    >
      <div
        v-if="openedResource"
        class="fixed inset-0 z-50 flex flex-col bg-black/60 backdrop-blur-sm p-4"
        @click.self="closeModal"
      >
        <div class="bg-white rounded-2xl flex flex-col overflow-hidden w-full max-w-4xl mx-auto h-full">

          <!-- Modal header -->
          <div class="flex items-center gap-3 px-5 py-3 border-b border-gray-100 shrink-0">
            <span class="text-xl">📄</span>
            <div class="flex-1 min-w-0">
              <h2 class="font-semibold text-indigo-950 truncate text-sm">{{ openedResource.name }}</h2>
            </div>
            <a
              :href="openedResource.file"
              target="_blank"
              class="text-xs font-medium text-indigo-500 hover:text-indigo-700 transition-colors no-underline shrink-0"
            >
              Open in new tab ↗
            </a>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer bg-transparent border-none text-lg shrink-0"
              @click="closeModal"
            >
              ✕
            </button>
          </div>

          <!-- Loading -->
          <div v-if="pdfLoading" class="flex-1 flex items-center justify-center">
            <div class="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>

          <!-- iframe -->
          <iframe
            v-else-if="pdfBlobUrl"
            :src="pdfBlobUrl"
            class="flex-1 w-full border-none"
          />
        </div>
      </div>
    </Transition>

  </div>
</template>
