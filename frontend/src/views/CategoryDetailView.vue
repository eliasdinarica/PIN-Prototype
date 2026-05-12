<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { InboxIcon, DocumentTextIcon, XMarkIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import ResourceList from '@/components/ResourceList.vue'
import CategorySidebarItem from '@/components/CategorySidebarItem.vue'
import CategoryMobilePill from '@/components/CategoryMobilePill.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const category = ref(null)
const categories = ref([])
const topResources = ref([])
const loading = ref(true)
const openedResource = ref(null)
const pdfBlobUrl = ref(null)
const pdfLoading = ref(false)

const isForYou = computed(() => route.params.id === 'for-you')

const recommendedCats = computed(() => categories.value.filter(c => c.is_recommended))
const otherCats = computed(() => categories.value.filter(c => !c.is_recommended))
const recommendedResources = computed(() => (category.value?.resources || []).filter(r => r.is_recommended))
const otherResources = computed(() => (category.value?.resources || []).filter(r => !r.is_recommended))

const categorySections = computed(() => {
  const s = []
  if (recommendedCats.value.length) s.push({ key: 'recommended', items: recommendedCats.value })
  if (otherCats.value.length) s.push({ key: 'others', items: otherCats.value })
  return s
})

const resourceSections = computed(() => {
  const s = []
  if (recommendedResources.value.length) s.push({ key: 'recommended', items: recommendedResources.value })
  if (otherResources.value.length) s.push({ key: 'others', items: otherResources.value })
  return s
})

const forYouSections = computed(() =>
  topResources.value.length ? [{ key: 'recommended', items: topResources.value }] : []
)

function getCategoryIcon(cat) {
  return HeroIcons[cat.icon] || HeroIcons.StarIcon
}

const categoryIcon = computed(() =>
  category.value ? getCategoryIcon(category.value) : null
)

function isActive(cat) {
  return String(cat.id) === String(route.params.id)
}

async function loadCategory(id) {
  if (id === 'for-you') { loading.value = false; return }
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
  const topUrl = profileId
    ? `http://localhost:8000/api/top-resources/?profile=${profileId}`
    : null

  const [allRes, topRes] = await Promise.all([
    fetch(listUrl),
    topUrl ? fetch(topUrl) : Promise.resolve(null),
  ])
  categories.value = await allRes.json()
  if (topRes) topResources.value = await topRes.json()

  const defaultId = topResources.value.length ? 'for-you' : categories.value[0]?.id
  const id = route.params.id || defaultId
  if (!id) { loading.value = false; return }

  if (!route.params.id) {
    router.replace(`/categories/${id}`)
    return
  }

  await loadCategory(id)
})

watch(() => route.params.id, (newId) => {
  if (newId && newId !== 'for-you') loadCategory(newId)
  else if (newId === 'for-you') { loading.value = false; category.value = null }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Mobile sticky header -->
    <div class="sticky top-0 z-10 bg-surface-800 border-b border-surface-700 lg:hidden">
      <div v-if="categories.length" class="flex items-center gap-2 px-4 py-3 overflow-x-auto pills-scroll">
        <CategoryMobilePill
          v-if="topResources.length"
          :label="t('categories.forYou')"
          :icon="SparklesIcon"
          :active="isForYou"
          @click="router.push('/categories/for-you')"
        />
        <template v-for="section in categorySections" :key="section.key">
          <div class="w-px h-6 bg-surface-600 shrink-0" />
          <CategoryMobilePill
            v-for="cat in section.items"
            :key="cat.id"
            :label="cat.name"
            :icon="getCategoryIcon(cat)"
            :active="isActive(cat)"
            :recommended="section.key === 'recommended'"
            @click="router.push(`/categories/${cat.id}`)"
          />
        </template>
      </div>
    </div>

    <!-- Main layout -->
    <div class="max-w-5xl mx-auto px-5 py-8 lg:flex lg:gap-8 lg:items-start">

      <!-- Desktop sidebar -->
      <aside v-if="categories.length" class="hidden lg:flex flex-col gap-1 w-56 shrink-0 sticky top-8">
        <CategorySidebarItem
          v-if="topResources.length"
          :label="t('categories.forYou')"
          :icon="SparklesIcon"
          :active="isForYou"
          class="mb-1"
          @click="router.push('/categories/for-you')"
        />
        <div v-if="topResources.length" class="mb-1 border-t border-surface-700/50" />
        <template v-for="(section, si) in categorySections" :key="section.key">
          <div v-if="si > 0" class="my-2 border-t border-surface-700/50" />
          <p
            v-if="section.key === 'recommended' || si > 0"
            class="text-xs font-semibold uppercase tracking-wider px-3 mb-1 flex items-center gap-1.5"
            :class="section.key === 'recommended' ? 'text-brand-400' : 'text-surface-500'"
          >
            <SparklesIcon v-if="section.key === 'recommended'" class="w-3.5 h-3.5" />
            {{ t(`categories.${section.key}`) }}
          </p>
          <CategorySidebarItem
            v-for="cat in section.items"
            :key="cat.id"
            :label="cat.name"
            :icon="getCategoryIcon(cat)"
            :active="isActive(cat)"
            @click="router.push(`/categories/${cat.id}`)"
          />
        </template>
      </aside>

      <!-- Resources content -->
      <div class="flex-1 min-w-0">

        <!-- For you view -->
        <template v-if="isForYou">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
              <SparklesIcon class="w-5 h-5 text-surface-600" />
            </div>
            <h1 class="text-2xl font-bold text-surface-800">{{ t('categories.forYou') }}</h1>
          </div>
          <p class="text-gray-500 text-sm mb-8 leading-relaxed">{{ t('categories.forYouDesc') }}</p>
          <ResourceList :sections="forYouSections" show-category @open="openResource" />
        </template>

        <template v-else>
          <!-- Category heading (desktop) -->
          <template v-if="category">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
                <component :is="categoryIcon" class="w-5 h-5 text-surface-600" />
              </div>
              <h1 class="text-2xl font-bold text-surface-800">{{ category.name }}</h1>
            </div>
            <p class="text-gray-500 text-sm mb-8 leading-relaxed">{{ category.description }}</p>
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

            <template v-else>
              <ResourceList :sections="resourceSections" @open="openResource" />
            </template>
          </template>
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
          <div class="flex items-center gap-3 px-5 py-3 bg-surface-500 border-b border-surface-400 shrink-0">
            <DocumentTextIcon class="w-5 h-5 text-surface-200 shrink-0" />
            <div class="flex-1 min-w-0">
              <h2 class="font-semibold text-white truncate text-sm">{{ openedResource.name }}</h2>
            </div>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-400 text-surface-300 hover:text-white transition-colors cursor-pointer bg-transparent border-none shrink-0"
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

<style scoped>
.pills-scroll::-webkit-scrollbar { display: none; }
.pills-scroll { scrollbar-width: none; }
</style>
