<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { InboxIcon, DocumentTextIcon, XMarkIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import ResourceCard from '@/components/ResourceCard.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const category = ref(null)
const categories = ref([])
const loading = ref(true)
const openedResource = ref(null)
const pdfBlobUrl = ref(null)
const pdfLoading = ref(false)

function getCategoryIcon(cat) {
  return HeroIcons[cat.icon] || HeroIcons.StarIcon
}

const categoryIcon = computed(() =>
  category.value ? getCategoryIcon(category.value) : null
)

async function loadCategory(id) {
  loading.value = true
  category.value = null
  try {
    const profileId = localStorage.getItem('profileId')
    const url = profileId
      ? `http://localhost:8000/api/categories/${id}/?profile=${profileId}`
      : `http://localhost:8000/api/categories/${id}/`
    const res = await fetch(url)
    category.value = await res.json()
  } finally {
    loading.value = false
  }
}

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
  const profileId = localStorage.getItem('profileId')
  const listUrl = profileId
    ? `http://localhost:8000/api/categories/?profile=${profileId}`
    : 'http://localhost:8000/api/categories/'
  const allRes = await fetch(listUrl)
  categories.value = await allRes.json()

  const id = route.params.id || categories.value[0]?.id
  if (!id) { loading.value = false; return }

  if (!route.params.id) {
    router.replace(`/categories/${id}`)
    return
  }

  await loadCategory(id)
})

watch(() => route.params.id, (newId) => {
  if (newId) loadCategory(newId)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Mobile sticky header: category pills -->
    <div class="sticky top-0 z-10 bg-surface-800 border-b border-surface-700 lg:hidden">
      <div v-if="categories.length" class="flex flex-wrap gap-2 px-4 py-3">
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="relative flex items-center gap-2 rounded-full border-2 transition-all duration-200 cursor-pointer"
          :class="String(cat.id) === String(route.params.id)
            ? 'bg-brand-600 border-brand-600 pl-3 pr-4 py-2'
            : 'bg-surface-700 border-surface-600 p-2.5 hover:border-surface-400'"
          @click="router.push(`/categories/${cat.id}`)"
        >
          <component
            :is="getCategoryIcon(cat)"
            class="w-5 h-5 shrink-0 transition-colors duration-200"
            :class="String(cat.id) === String(route.params.id) ? 'text-white' : 'text-surface-300'"
          />
          <span
            v-if="String(cat.id) === String(route.params.id)"
            class="text-white text-sm font-semibold whitespace-nowrap"
          >{{ cat.name }}</span>
          <SparklesIcon
            v-if="cat.is_recommended && String(cat.id) === String(route.params.id)"
            class="w-3 h-3 text-white/70 shrink-0"
          />
          <!-- dot indicator for inactive recommended pills -->
          <span
            v-if="cat.is_recommended && String(cat.id) !== String(route.params.id)"
            class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-brand-500 border-2 border-surface-800 rounded-full"
          />
        </button>
      </div>
    </div>

    <!-- Main layout -->
    <div class="max-w-5xl mx-auto px-5 py-8 lg:flex lg:gap-8 lg:items-start">

      <!-- Desktop sidebar -->
      <aside v-if="categories.length" class="hidden lg:flex flex-col gap-1 w-56 shrink-0 sticky top-8">
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer border-2 text-left w-full"
          :class="String(cat.id) === String(route.params.id)
            ? 'bg-surface-700 text-white border-surface-700'
            : 'bg-surface-800/40 text-surface-200 border-transparent hover:bg-surface-800 hover:text-white'"
          @click="router.push(`/categories/${cat.id}`)"
        >
          <div
            class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            :class="String(cat.id) === String(route.params.id) ? 'bg-white/20' : 'bg-surface-700'"
          >
            <component
              :is="getCategoryIcon(cat)"
              class="w-4 h-4"
              :class="String(cat.id) === String(route.params.id) ? 'text-white' : 'text-surface-300'"
            />
          </div>
          <span class="truncate flex-1">{{ cat.name }}</span>
          <SparklesIcon
            v-if="cat.is_recommended"
            class="w-3.5 h-3.5 shrink-0"
            :class="String(cat.id) === String(route.params.id) ? 'text-white/60' : 'text-brand-400'"
          />
        </button>
      </aside>

      <!-- Resources content -->
      <div class="flex-1 min-w-0">

        <!-- Category heading (desktop) -->
        <template v-if="category">
          <div class="hidden lg:flex items-center gap-3 mb-2">
            <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
              <component :is="categoryIcon" class="w-5 h-5 text-surface-600" />
            </div>
            <h1 class="text-2xl font-bold text-surface-800">{{ category.name }}</h1>
          </div>
          <p class="text-gray-500 text-sm mb-8 leading-relaxed lg:pl-12">{{ category.description }}</p>
        </template>

        <!-- Loading -->
        <div v-if="loading" class="flex justify-center py-20">
          <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
        </div>

        <template v-else-if="category">
          <!-- Empty -->
          <div v-if="category.resources.length === 0" class="bg-surface-500 rounded-2xl p-12 text-center shadow-sm">
            <InboxIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p class="text-gray-400 text-sm">{{ t('detail.empty') }}</p>
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
        </template>

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
            <DocumentTextIcon class="w-5 h-5 text-surface-400 shrink-0" />
            <div class="flex-1 min-w-0">
              <h2 class="font-semibold text-surface-800 truncate text-sm">{{ openedResource.name }}</h2>
            </div>
            <a
              :href="openedResource.file"
              target="_blank"
              class="text-xs font-medium text-surface-500 hover:text-surface-700 transition-colors no-underline shrink-0"
            >
              {{ t('detail.openTab') }}
            </a>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer bg-transparent border-none shrink-0"
              @click="closeModal"
            >
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>

          <!-- Loading -->
          <div v-if="pdfLoading" class="flex-1 flex items-center justify-center">
            <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
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
