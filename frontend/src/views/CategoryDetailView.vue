<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { InboxIcon, DocumentTextIcon, XMarkIcon, SparklesIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline'
import ResourceList from '@/components/ResourceList.vue'
import CategorySidebarItem from '@/components/CategorySidebarItem.vue'
import CategoryMobilePill from '@/components/CategoryMobilePill.vue'
import ArticleRenderer from '@/components/ArticleRenderer.vue'
import OnboardingTutorial from '@/components/OnboardingTutorial.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const category = ref(null)
const categories = ref([])
const topResources = ref([])
const feedbackMap = ref({}) // { [resource_id]: { id, is_useful } }
const loading = ref(true)
const openedResource = ref(null)
const activePillEl = ref(null)
const pillsScrollRef = ref(null)
const otherPillsRef = ref(null)
const visibleSection = ref('recommended')

function onPillsScroll() {
  const container = pillsScrollRef.value
  const othersDiv = otherPillsRef.value
  if (!container || !othersDiv) return
  const viewportCenter = container.scrollLeft + container.offsetWidth / 2
  visibleSection.value = viewportCenter >= othersDiv.offsetLeft ? 'others' : 'recommended'
}

const isForYou = computed(() => route.params.id === 'for-you')

const categorySections = computed(() => {
  const rec = categories.value.filter(c => c.is_recommended)
  const oth = categories.value.filter(c => !c.is_recommended)
  const s = []
  if (rec.length) s.push({ key: 'recommended', items: rec })
  if (oth.length) s.push({ key: 'others', items: oth })
  return s
})

const resourceSections = computed(() => {
  const resources = category.value?.resources || []
  const rec = resources.filter(r => r.is_recommended)
  const oth = resources.filter(r => !r.is_recommended)
  const s = []
  if (rec.length) s.push({ key: 'recommended', items: rec })
  if (oth.length) s.push({ key: 'others', items: oth })
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
      ? `${API}/api/categories/${id}/?profile=${profileId}`
      : `${API}/api/categories/${id}/`
    const res = await fetch(url)
    category.value = await res.json()
  } finally {
    loading.value = false
  }
}

function openResource(resource) {
  openedResource.value = resource
}

function closeModal() {
  openedResource.value = null
}

function filenameFromUrl(url) {
  try { return decodeURIComponent(url.split('/').pop().split('?')[0]) } catch { return url }
}

async function handleFeedbackChange({ resourceId, feedbackId, isUseful }) {
  const profileId = localStorage.getItem('profileId')
  if (!profileId) return

  if (isUseful === null) {
    await fetch(`${API}/api/feedback/${feedbackId}/`, { method: 'DELETE' })
    const map = { ...feedbackMap.value }
    delete map[resourceId]
    feedbackMap.value = map
  } else {
    const res = await fetch(`${API}/api/feedback/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile: parseInt(profileId), resource: resourceId, is_useful: isUseful }),
    })
    const data = await res.json()
    feedbackMap.value = { ...feedbackMap.value, [resourceId]: { id: data.id, is_useful: data.is_useful } }
  }

  // Re-fetch scores so similar resources update their is_recommended status
  const catId = route.params.id
  const topUrl = `${API}/api/top-resources/?profile=${profileId}`
  const [catRes, topRes] = await Promise.all([
    catId && catId !== 'for-you'
      ? fetch(`${API}/api/categories/${catId}/?profile=${profileId}`)
      : Promise.resolve(null),
    fetch(topUrl),
  ])
  if (catRes) category.value = await catRes.json()
  if (topRes) topResources.value = await topRes.json()
}

onMounted(async () => {
  const profileId = localStorage.getItem('profileId')
  const listUrl = profileId
    ? `${API}/api/categories/?profile=${profileId}`
    : `${API}/api/categories/`
  const topUrl = profileId
    ? `${API}/api/top-resources/?profile=${profileId}`
    : null
  const fbUrl = profileId
    ? `${API}/api/feedback/?profile=${profileId}`
    : null

  const [allRes, topRes, fbRes] = await Promise.all([
    fetch(listUrl),
    topUrl ? fetch(topUrl) : Promise.resolve(null),
    fbUrl ? fetch(fbUrl) : Promise.resolve(null),
  ])
  categories.value = await allRes.json()
  if (topRes) topResources.value = await topRes.json()
  if (fbRes) {
    const fbData = await fbRes.json()
    feedbackMap.value = Object.fromEntries(
      fbData.map(fb => [fb.resource, { id: fb.id, is_useful: fb.is_useful }])
    )
  }

  const defaultId = topResources.value.length ? 'for-you' : categories.value[0]?.id
  const id = route.params.id || defaultId
  if (!id) { loading.value = false; return }

  if (!route.params.id) {
    router.replace(`/categories/${id}`)
    return
  }

  await loadCategory(id)
})

function scrollPillToCenter(el) {
  const container = pillsScrollRef.value
  if (!container || !el) return
  const scrollLeft = el.offsetLeft - (container.offsetWidth - el.offsetWidth) / 2
  container.scrollTo({ left: scrollLeft, behavior: 'smooth' })
}

watch(() => route.params.id, async (newId) => {
  if (newId && newId !== 'for-you') loadCategory(newId)
  else if (newId === 'for-you') { loading.value = false; category.value = null }
  await nextTick()
  scrollPillToCenter(activePillEl.value?.$el ?? activePillEl.value)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Mobile sticky header -->
    <div class="sticky top-0 z-20 bg-surface-800 border-b border-surface-700 lg:hidden">
      <div v-if="categories.length">

        <!-- Label de section dynamique -->
        <div class="px-4 pt-3 pb-1">
          <p
            v-if="visibleSection === 'others'"
            class="text-xs font-semibold uppercase tracking-wider text-surface-500"
          >{{ t('categories.others') }}</p>
          <p
            v-else
            class="text-xs font-semibold uppercase tracking-wider text-brand-400 flex items-center gap-1"
          ><SparklesIcon class="w-3 h-3" />{{ t('categories.recommended') }}</p>
        </div>

        <!-- Scrollable pills -->
        <div
          ref="pillsScrollRef"
          data-tut="cats-mobile"
          class="flex items-center gap-2 px-4 pb-4 overflow-x-auto pills-scroll"
          @scroll="onPillsScroll"
        >
          <!-- Recommended pills -->
          <div class="flex gap-2 shrink-0">
            <CategoryMobilePill
              v-if="topResources.length"
              :ref="isForYou ? el => { activePillEl = el } : undefined"
              :label="t('categories.forYou')"
              :icon="SparklesIcon"
              :active="isForYou"
              @click="router.push('/categories/for-you')"
            />
            <CategoryMobilePill
              v-for="cat in (categorySections.find(s => s.key === 'recommended')?.items ?? [])"
              :key="cat.id"
              :ref="isActive(cat) ? el => { activePillEl = el } : undefined"
              :label="cat.name"
              :icon="getCategoryIcon(cat)"
              :active="isActive(cat)"
              @click="router.push(`/categories/${cat.id}`)"
            />
          </div>

          <!-- Divider + Others pills -->
          <template v-if="categorySections.some(s => s.key === 'others')">
            <div class="w-px h-7 bg-surface-600 shrink-0" />
            <div ref="otherPillsRef" class="flex gap-2 shrink-0">
              <CategoryMobilePill
                v-for="cat in (categorySections.find(s => s.key === 'others')?.items ?? [])"
                :key="cat.id"
                :ref="isActive(cat) ? el => { activePillEl = el } : undefined"
                :label="cat.name"
                :icon="getCategoryIcon(cat)"
                :active="isActive(cat)"
                @click="router.push(`/categories/${cat.id}`)"
              />
            </div>
          </template>
        </div>

      </div>
    </div>

    <!-- Main layout -->
    <div class="max-w-5xl mx-auto px-5 py-8 lg:flex lg:gap-8 lg:items-start">

      <!-- Desktop sidebar -->
      <aside v-if="categories.length" data-tut="cats-desktop" class="hidden lg:flex flex-col gap-1 w-56 shrink-0 sticky top-8">
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
          <ResourceList :sections="forYouSections" show-category :feedback-map="feedbackMap" @open="openResource" @feedback-change="handleFeedbackChange" />
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
              <ResourceList :sections="resourceSections" :feedback-map="feedbackMap" @open="openResource" @feedback-change="handleFeedbackChange" />
            </template>
          </template>
        </template>

      </div>
    </div>

    <OnboardingTutorial />

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
        <div class="bg-white rounded-2xl flex flex-col overflow-hidden w-full max-w-3xl mx-auto h-full">

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

          <!-- Article body -->
          <div class="flex-1 overflow-y-auto overflow-x-hidden px-6 py-6">
            <div class="max-w-2xl mx-auto min-w-0">
              <!-- Description always shown as intro -->
              <p v-if="openedResource.description" class="text-surface-600 leading-relaxed mb-6">{{ openedResource.description }}</p>

              <!-- Article body only if there is real content -->
              <ArticleRenderer
                v-if="openedResource.body?.sections?.length || openedResource.body?.blocks?.length"
                :body="openedResource.body"
              />

              <!-- Attachments -->
              <div v-if="openedResource.attachments?.length" class="mt-8 pt-6 border-t border-surface-200">
                <p class="text-xs font-semibold uppercase tracking-wider text-surface-500 mb-3">Files</p>
                <div class="space-y-2">
                  <a
                    v-for="a in openedResource.attachments"
                    :key="a.id"
                    :href="a.file"
                    target="_blank"
                    download
                    class="flex items-center gap-3 p-3 rounded-xl border border-surface-200 hover:border-brand-400 hover:bg-brand-50 transition-colors no-underline"
                  >
                    <DocumentTextIcon class="w-5 h-5 text-brand-500 shrink-0" />
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-surface-800 text-sm truncate">{{ a.label || filenameFromUrl(a.file) }}</p>
                      <p v-if="a.label" class="text-xs text-surface-500 truncate">{{ filenameFromUrl(a.file) }}</p>
                    </div>
                    <ArrowDownTrayIcon class="w-4 h-4 text-surface-400 shrink-0" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.pills-scroll::-webkit-scrollbar { display: none; }
.pills-scroll { scrollbar-width: none; }
</style>
