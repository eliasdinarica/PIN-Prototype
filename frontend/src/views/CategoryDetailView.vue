<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { InboxIcon, SparklesIcon, MagnifyingGlassIcon, ArrowLeftIcon, BookmarkIcon } from '@heroicons/vue/24/outline'
import ResourceList from '@/components/ResourceList.vue'
import CategorySidebarItem from '@/components/CategorySidebarItem.vue'
import CategoryMobilePill from '@/components/CategoryMobilePill.vue'
import { useSaved } from '@/composables/useSaved'

const route = useRoute()
const router = useRouter()
const { t, tm } = useI18n()
const { savedIds } = useSaved()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const category = ref(null)
const categories = ref([])
const topResources = ref([])
const savedResourcesData = ref([])
const feedbackMap = ref({}) // { [resource_id]: { id, is_useful } }
const loading = ref(true)
const activePillEl = ref(null)
const pillsScrollRef = ref(null)

const isForYou = computed(() => route.params.id === 'for-you')
const isAiSearch = computed(() => route.params.id === 'ai')
const isSavedView = computed(() => route.params.id === 'saved')
const initialResourceId = computed(() => route.query.resource ? parseInt(route.query.resource) : null)

const aiEditableQuery = ref('')
const aiQuery = ref('')
const aiReply = ref('')
const aiResources = ref([])
const aiPathways = ref([])
const aiLoading = ref(false)
const aiError = ref('')
// Tag pathways so the list renders them as a pathway card (with its badge).
const asPathwayItems = (pathways) => (pathways || []).map(p => ({ ...p, _kind: 'pathway' }))

const aiSections = computed(() => {
  const items = [...asPathwayItems(aiPathways.value), ...aiResources.value]
  return items.length ? [{ key: 'all', items }] : []
})


const resourceSections = computed(() => {
  const resources = category.value?.resources || []
  const pathways = asPathwayItems(category.value?.pathways)
  if (!resources.length && !pathways.length) return []

  // Group by subcategory (resources already sorted by score from backend)
  const grouped = new Map()
  for (const r of resources) {
    const key = r.subcategory ? String(r.subcategory.id) : '__none__'
    if (!grouped.has(key)) {
      grouped.set(key, {
        key: 'subcategory',
        label: r.subcategory?.name ?? null,
        order: r.subcategory?.order ?? 999,
        items: [],
      })
    }
    grouped.get(key).items.push(r)
  }

  let groups = [...grouped.values()].sort((a, b) => a.order - b.order)

  // Single resource group with no label → flat list, no header
  if (groups.length === 1 && groups[0].label === null) {
    groups = [{ key: 'all', items: resources }]
  }

  // Pathways are mixed in with the resources (top of the list), no separate header.
  if (pathways.length) {
    if (groups.length) groups[0] = { ...groups[0], items: [...pathways, ...groups[0].items] }
    else groups = [{ key: 'all', items: pathways }]
  }

  return groups
})

const forYouSections = computed(() =>
  topResources.value.length ? [{ key: 'recommended', items: topResources.value }] : []
)

const savedSections = computed(() =>
  savedResourcesData.value.length ? [{ key: 'all', items: savedResourcesData.value }] : []
)

async function loadSaved() {
  const ids = savedIds.value
  if (!ids.length) { savedResourcesData.value = []; return }
  const results = await Promise.all(
    ids.map(id => fetch(`${API}/api/resources/${id}/`).then(r => r.ok ? r.json() : null).catch(() => null))
  )
  // Keep saved order, drop any that no longer exist
  savedResourcesData.value = results.filter(Boolean)
}

function getCategoryIcon(cat) {
  return HeroIcons[cat.icon] || HeroIcons.StarIcon
}

const categoryIcon = computed(() =>
  category.value ? getCategoryIcon(category.value) : null
)

function isActive(cat) {
  return String(cat.id) === String(route.params.id)
}

async function runAiSearch(q) {
  if (!q?.trim()) return
  aiLoading.value = true
  aiReply.value = ''
  aiResources.value = []
  aiPathways.value = []
  aiError.value = ''
  aiQuery.value = q
  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q, history: [] }),
    })
    const data = await res.json()
    if (data.error) aiError.value = data.error
    else { aiReply.value = data.reply; aiResources.value = data.resources || []; aiPathways.value = data.pathways || [] }
  } catch {
    aiError.value = 'Connection error. Please try again.'
  }
  aiLoading.value = false
}

function submitAiSearch() {
  const q = aiEditableQuery.value.trim()
  if (!q) return
  router.push(`/categories/ai?q=${encodeURIComponent(q)}`)
}

function onAiKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitAiSearch() }
}

async function loadCategory(id) {
  if (id === 'for-you' || id === 'ai' || id === 'saved') { loading.value = false; return }
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

  if (route.params.id === 'saved') await loadSaved()

  if (route.params.id === 'ai' && route.query.q) {
    aiEditableQuery.value = route.query.q
    runAiSearch(route.query.q)
  }
})

function scrollPillToCenter(el) {
  const container = pillsScrollRef.value
  if (!container || !el) return
  const scrollLeft = el.offsetLeft - (container.offsetWidth - el.offsetWidth) / 2
  container.scrollTo({ left: scrollLeft, behavior: 'smooth' })
}

watch(() => route.params.id, async (newId) => {
  if (newId === 'ai' || newId === 'for-you') { loading.value = false; category.value = null }
  else if (newId === 'saved') { loading.value = false; category.value = null; loadSaved() }
  else if (newId) loadCategory(newId)
  await nextTick()
  scrollPillToCenter(activePillEl.value?.$el ?? activePillEl.value)
})

// Keep the saved list fresh when items are added/removed while viewing it.
watch(savedIds, () => { if (isSavedView.value) loadSaved() }, { deep: true })

watch(() => route.query.q, (newQ) => {
  if (isAiSearch.value && newQ) {
    aiEditableQuery.value = newQ
    runAiSearch(newQ)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200 lg:flex">

    <!-- Desktop left grey panel (hidden on mobile) -->
    <aside v-if="categories.length" data-tut="cats-desktop" class="hidden lg:flex flex-col w-100 shrink-0 bg-surface-500 border-r border-surface-400">
      <div class="sticky top-0 h-screen py-4 px-4 flex flex-col gap-0.5">
        <button
          class="flex items-center gap-1.5 text-xs font-medium text-surface-300 hover:text-white transition-colors cursor-pointer bg-transparent border-none mb-3 px-2 py-1 self-start"
          @click="router.push('/hub')"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5" />
          Hub
        </button>
        <CategorySidebarItem
          v-if="topResources.length"
          :label="t('categories.forYou')"
          :icon="SparklesIcon"
          :active="isForYou"
          class="mb-1"
          @click="router.push('/categories/for-you')"
        />
        <CategorySidebarItem
          :label="t('categories.aiSearch')"
          :icon="MagnifyingGlassIcon"
          :active="isAiSearch"
          class="mb-1"
          @click="router.push('/categories/ai')"
        />
        <CategorySidebarItem
          :label="t('categories.saved')"
          :icon="BookmarkIcon"
          :active="isSavedView"
          class="mb-1"
          @click="router.push('/categories/saved')"
        />
        <div class="mb-2 border-t border-surface-400" />
        <CategorySidebarItem
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :icon="getCategoryIcon(cat)"
          :active="isActive(cat)"
          @click="router.push(`/categories/${cat.id}`)"
        />
      </div>
    </aside>

    <!-- Right panel: full width on mobile, flex-1 on desktop -->
    <div class="flex-1 min-w-0">

    <!-- Mobile sticky header -->
    <div class="sticky top-0 z-20 bg-surface-800 border-b border-surface-700 lg:hidden">

      <!-- Back to hub -->
      <div class="px-4 pt-2.5 pb-1">
        <button
          class="flex items-center gap-1 text-xs text-surface-400 hover:text-surface-200 transition-colors cursor-pointer bg-transparent border-none p-0"
          @click="router.push('/hub')"
        >
          <ArrowLeftIcon class="w-3 h-3" />
          Hub
        </button>
      </div>

      <!-- AI sticky query (shown when on AI page with an active query) -->
      <div v-if="isAiSearch && aiQuery" class="px-4 py-2.5 flex items-center gap-2 border-b border-surface-700">
        <MagnifyingGlassIcon class="w-4 h-4 text-brand-400 shrink-0" />
        <span class="flex-1 text-surface-200 text-sm truncate italic">{{ aiQuery }}</span>
      </div>

      <div v-if="categories.length">

        <!-- Label de section dynamique -->
        <div v-if="isAiSearch" class="px-4 pt-3 pb-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-brand-400 flex items-center gap-1">
            <MagnifyingGlassIcon class="w-3 h-3" />{{ t('categories.aiSearch') }}
          </p>
        </div>

        <!-- Scrollable pills -->
        <div
          ref="pillsScrollRef"
          data-tut="cats-mobile"
          class="flex items-center gap-2 px-4 pb-4 overflow-x-auto pills-scroll"
        >
          <CategoryMobilePill
            v-if="topResources.length"
            :ref="isForYou ? el => { activePillEl = el } : undefined"
            :label="t('categories.forYou')"
            :icon="SparklesIcon"
            :active="isForYou"
            @click="router.push('/categories/for-you')"
          />
          <CategoryMobilePill
            :ref="isAiSearch ? el => { activePillEl = el } : undefined"
            :label="t('categories.aiSearch')"
            :icon="MagnifyingGlassIcon"
            :active="isAiSearch"
            @click="router.push('/categories/ai')"
          />
          <CategoryMobilePill
            :ref="isSavedView ? el => { activePillEl = el } : undefined"
            :label="t('categories.saved')"
            :icon="BookmarkIcon"
            :active="isSavedView"
            @click="router.push('/categories/saved')"
          />
          <CategoryMobilePill
            v-for="cat in categories"
            :key="cat.id"
            :ref="isActive(cat) ? el => { activePillEl = el } : undefined"
            :label="cat.name"
            :icon="getCategoryIcon(cat)"
            :active="isActive(cat)"
            @click="router.push(`/categories/${cat.id}`)"
          />
        </div>

      </div>
    </div>

    <!-- Content -->
    <div class="max-w-4xl mx-auto px-5 py-8">

        <!-- AI Search view -->
        <template v-if="isAiSearch">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
              <MagnifyingGlassIcon class="w-5 h-5 text-surface-600" />
            </div>
            <h1 class="text-2xl font-bold text-surface-800">{{ t('categories.aiSearch') }}</h1>
          </div>

          <div class="flex items-start gap-2 mb-8">
            <textarea
              v-model="aiEditableQuery"
              rows="1"
              :placeholder="t('categories.aiPlaceholder')"
              class="flex-1 resize-none text-surface-800 text-sm border border-surface-200 rounded-xl px-4 py-2.5 outline-none focus:border-brand-400 transition-colors bg-white placeholder-surface-400 leading-snug"
              style="max-height: 96px; overflow-y: auto;"
              @keydown="onAiKeydown"
            />
            <button
              :disabled="!aiEditableQuery.trim() || aiLoading"
              class="h-10 px-4 bg-brand-500 hover:bg-brand-600 disabled:bg-surface-200 text-white rounded-xl text-sm font-medium transition-colors cursor-pointer border-none shrink-0"
              @click="submitAiSearch"
            >{{ t('categories.aiSubmit') }}</button>
          </div>

          <!-- Suggestion chips — visible only before any search -->
          <div v-if="!aiQuery && !aiLoading" class="flex flex-wrap gap-2 mb-6">
            <button
              v-for="s in (tm('categories.aiSuggestions'))"
              :key="s"
              class="text-sm px-4 py-2 rounded-full border border-surface-300 bg-white text-surface-600 hover:border-brand-400 hover:text-brand-500 transition-colors cursor-pointer"
              @click="aiEditableQuery = s; submitAiSearch()"
            >{{ s }}</button>
          </div>

          <div v-if="aiLoading" class="flex justify-center py-20">
            <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
          </div>
          <p v-else-if="aiError" class="text-red-500 text-sm">{{ aiError }}</p>
          <template v-else-if="aiReply || aiResources.length">
            <p v-if="aiReply" class="text-gray-500 text-sm mb-8 leading-relaxed">{{ aiReply }}</p>
            <div v-if="!aiSections.length" class="bg-surface-500 rounded-2xl p-12 text-center shadow-sm">
              <InboxIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p class="text-gray-400 text-sm">{{ t('detail.empty') }}</p>
            </div>
            <ResourceList v-else :sections="aiSections" show-category :feedback-map="{}" />
          </template>
        </template>

        <!-- For you view -->
        <template v-else-if="isForYou">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
              <SparklesIcon class="w-5 h-5 text-surface-600" />
            </div>
            <h1 class="text-2xl font-bold text-surface-800">{{ t('categories.forYou') }}</h1>
          </div>
          <p class="text-gray-500 text-sm mb-8 leading-relaxed">{{ t('categories.forYouDesc') }}</p>
          <ResourceList :sections="forYouSections" show-category :feedback-map="feedbackMap" :initial-resource-id="initialResourceId" @feedback-change="handleFeedbackChange" />
        </template>

        <!-- Saved view -->
        <template v-else-if="isSavedView">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-9 h-9 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
              <BookmarkIcon class="w-5 h-5 text-surface-600" />
            </div>
            <h1 class="text-2xl font-bold text-surface-800">{{ t('categories.saved') }}</h1>
          </div>
          <p class="text-gray-500 text-sm mb-8 leading-relaxed">{{ t('categories.savedDesc') }}</p>
          <div v-if="!savedSections.length" class="bg-surface-500 rounded-2xl p-12 text-center shadow-sm">
            <BookmarkIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p class="text-gray-400 text-sm">{{ t('categories.savedEmpty') }}</p>
          </div>
          <ResourceList v-else :sections="savedSections" show-category :feedback-map="feedbackMap" :initial-resource-id="initialResourceId" @feedback-change="handleFeedbackChange" />
        </template>

        <template v-else>
          <!-- Category heading -->
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
              <ResourceList :sections="resourceSections" :feedback-map="feedbackMap" :initial-resource-id="initialResourceId" @feedback-change="handleFeedbackChange" />
            </template>
          </template>
        </template>

    </div>

    </div>

  </div>
</template>

<style scoped>
.pills-scroll::-webkit-scrollbar { display: none; }
.pills-scroll { scrollbar-width: none; }
</style>
