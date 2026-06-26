<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { ArrowLeftIcon, PlusIcon, XMarkIcon, ChevronDownIcon, InboxIcon, SparklesIcon, PaperAirplaneIcon, TagIcon, CheckIcon } from '@heroicons/vue/24/outline'
import ResourceList from '@/components/ResourceList.vue'
import { useSaved } from '@/composables/useSaved'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { savedIds } = useSaved()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const categories = ref([])
const resources = ref([])
const guides = ref([])
const feedbackMap = ref({})
const loading = ref(true)

const selectedThemes = ref([])      // category ids
const activeTab = ref('all')        // all | resources | pathways | saved
const themeMenuOpen = ref(false)

// Optional AI search (not mandatory; filters work on their own).
const aiOpen = ref(false)
const aiInput = ref('')
const aiLoading = ref(false)
const aiReply = ref('')
const aiResources = ref([])
const aiGuides = ref([])
const aiActive = ref(false)

const initialResourceId = computed(() => route.query.resource ? parseInt(route.query.resource) : null)

const TABS = ['all', 'resources', 'pathways', 'saved']

const expandedCat = ref(null)  // category id whose subcategories are shown
const topicMenuRef = ref(null)

// Persist selected topics across refreshes.
try {
  const saved = JSON.parse(localStorage.getItem('searchThemes') || '[]')
  if (Array.isArray(saved)) selectedThemes.value = saved
} catch { /* ignore */ }
watch(selectedThemes, (v) => localStorage.setItem('searchThemes', JSON.stringify(v)), { deep: true })

function onDocClick(e) {
  if (themeMenuOpen.value && topicMenuRef.value && !topicMenuRef.value.contains(e.target)) {
    themeMenuOpen.value = false
  }
}
onMounted(() => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))

function getCategoryIcon(cat) {
  return HeroIcons[cat.icon] || HeroIcons.StarIcon
}

// selectedThemes holds { type:'cat'|'sub', id, name, icon?, categoryId? }
function isSelected(type, id) {
  return selectedThemes.value.some(s => s.type === type && s.id === id)
}
function toggleSel(item) {
  if (isSelected(item.type, item.id)) {
    selectedThemes.value = selectedThemes.value.filter(s => !(s.type === item.type && s.id === item.id))
    return
  }
  let next = [...selectedThemes.value]
  if (item.type === 'cat') {
    // The whole category already covers its subtopics — drop them.
    next = next.filter(s => !(s.type === 'sub' && s.categoryId === item.id))
  } else {
    // Picking a specific subtopic narrows the whole-category selection.
    next = next.filter(s => !(s.type === 'cat' && s.id === item.categoryId))
  }
  selectedThemes.value = [...next, item]
}

// Whole-category chips, and subcategory chips grouped under their parent.
const groupedSelection = computed(() => {
  const cats = selectedThemes.value.filter(s => s.type === 'cat')
  const map = {}
  for (const s of selectedThemes.value) {
    if (s.type !== 'sub') continue
    const cat = categories.value.find(c => c.id === s.categoryId)
    if (!map[s.categoryId]) map[s.categoryId] = { categoryId: s.categoryId, name: cat?.name || '', icon: cat?.icon, subs: [] }
    map[s.categoryId].subs.push(s)
  }
  return { cats, groups: Object.values(map) }
})

const selectedCatIds = computed(() => selectedThemes.value.filter(s => s.type === 'cat').map(s => s.id))
const selectedSubIds = computed(() => selectedThemes.value.filter(s => s.type === 'sub').map(s => s.id))
// Categories that should also surface pathways (whole cat or parent of a chosen sub).
const activeCatIds = computed(() => new Set([
  ...selectedCatIds.value,
  ...selectedThemes.value.filter(s => s.type === 'sub').map(s => s.categoryId),
]))

function matchesResource(r) {
  if (!selectedThemes.value.length) return true
  if (r.category && selectedCatIds.value.includes(r.category.id)) return true
  if (r.subcategory && selectedSubIds.value.includes(r.subcategory.id)) return true
  return false
}
function matchesGuide(g) {
  if (!selectedThemes.value.length) return true
  return g.category && activeCatIds.value.has(g.category.id)
}

// Items, tagged so the list renders the right card.
const guideItems = computed(() => guides.value.map(g => ({ ...g, _kind: 'guide' })))

// A recommended item (guide or resource) bubbles to the top regardless of type.
function isRecommended(it) {
  return !!(it.recommended_by_system || it.recommended_by_similar || it.recommended_by_affinity)
}
// Stable sort keeps the backend's per-type ranking, but puts recommended first.
function recommendedFirst(items) {
  return [...items].sort((a, b) => (isRecommended(b) ? 1 : 0) - (isRecommended(a) ? 1 : 0))
}

const results = computed(() => {
  if (aiActive.value) {
    return [...aiGuides.value.map(g => ({ ...g, _kind: 'guide' })), ...aiResources.value]
  }
  const res = resources.value.filter(matchesResource)
  const gd = guideItems.value.filter(matchesGuide)
  if (activeTab.value === 'resources') return res
  if (activeTab.value === 'pathways') return gd
  if (activeTab.value === 'saved') {
    return recommendedFirst([
      ...gd.filter(g => savedIds.value.includes(`g:${g.id}`)),
      ...res.filter(r => savedIds.value.includes(r.id)),
    ])
  }
  return recommendedFirst([...gd, ...res])
})

const sections = computed(() => results.value.length ? [{ key: 'all', items: results.value }] : [])

async function runAi() {
  const q = aiInput.value.trim()
  if (!q) return
  aiLoading.value = true
  aiReply.value = ''; aiResources.value = []; aiGuides.value = []
  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q, history: [] }),
    })
    const data = await res.json()
    if (!data.error) {
      aiReply.value = data.reply
      aiResources.value = data.resources || []
      aiGuides.value = data.guides || []
      aiActive.value = true
    }
  } catch { /* ignore */ }
  aiLoading.value = false
}

function clearAi() {
  aiActive.value = false; aiOpen.value = false
  aiReply.value = ''; aiInput.value = ''; aiResources.value = []; aiGuides.value = []
}

async function handleFeedbackChange({ resourceId, feedbackId, isUseful }) {
  const profileId = localStorage.getItem('profileId')
  if (!profileId) return
  if (isUseful === null) {
    await fetch(`${API}/api/feedback/${feedbackId}/`, { method: 'DELETE' })
    const map = { ...feedbackMap.value }; delete map[resourceId]; feedbackMap.value = map
  } else {
    const res = await fetch(`${API}/api/feedback/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile: parseInt(profileId), resource: resourceId, is_useful: isUseful }),
    })
    const data = await res.json()
    feedbackMap.value = { ...feedbackMap.value, [resourceId]: { id: data.id, is_useful: data.is_useful } }
  }
}

onMounted(async () => {
  const profileId = localStorage.getItem('profileId')
  // Send saved resource ids so the backend can boost similar ones (affinity).
  const savedResIds = savedIds.value.filter(x => /^\d+$/.test(String(x)))
  const params = new URLSearchParams()
  if (profileId) params.set('profile', profileId)
  if (savedResIds.length) params.set('saved', savedResIds.join(','))
  const qs = params.toString()
  const [searchRes, fbRes] = await Promise.all([
    fetch(`${API}/api/search/${qs ? `?${qs}` : ''}`),
    profileId ? fetch(`${API}/api/feedback/?profile=${profileId}`) : Promise.resolve(null),
  ])
  const data = await searchRes.json()
  categories.value = data.categories || []
  resources.value = data.resources || []
  guides.value = data.guides || []
  if (fbRes) {
    const fb = await fbRes.json()
    feedbackMap.value = Object.fromEntries(fb.map(f => [f.resource, { id: f.id, is_useful: f.is_useful }]))
  }
  loading.value = false
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Header with the first-person sentence -->
    <header class="bg-brand-50/60 border-b border-surface-200">
      <div class="max-w-3xl mx-auto px-5 pt-8 pb-7">
        <button
          class="flex items-center gap-1.5 text-xs font-medium text-surface-500 hover:text-surface-700 mb-5 cursor-pointer bg-transparent border-none p-0 transition-colors"
          @click="router.push('/hub')"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5" />Hub
        </button>

        <h1 class="text-2xl sm:text-3xl font-bold text-surface-800 mb-5">{{ t('search.title') }}</h1>

        <!-- Composed sentence + add-topic (stacked on mobile, pinned right on desktop) -->
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
          <div class="flex flex-wrap items-center gap-2 text-lg sm:text-xl text-surface-700 leading-relaxed flex-1 min-w-0">
          <span>{{ t('search.sentenceStart') }}</span>
          <span class="font-semibold text-surface-900">{{ t(`search.type.${activeTab}`) }}</span>
          <span>{{ t('search.on') }}</span>

          <span v-if="!selectedThemes.length" class="text-surface-400 italic">{{ t('search.anyTopic') }}</span>

          <!-- Whole-category chips -->
          <button
            v-for="cat in groupedSelection.cats"
            :key="'cat' + cat.id"
            class="inline-flex items-center gap-1.5 bg-brand-500 text-white rounded-full pl-3 pr-2 py-1 text-sm font-medium cursor-pointer border-none hover:bg-brand-600 transition-colors"
            @click="toggleSel(cat)"
          >
            <component :is="HeroIcons[cat.icon] || HeroIcons.StarIcon" class="w-3.5 h-3.5" />
            {{ cat.name }}
            <XMarkIcon class="w-4 h-4" />
          </button>

          <!-- Subcategories grouped under their category -->
          <span
            v-for="grp in groupedSelection.groups"
            :key="'grp' + grp.categoryId"
            class="inline-flex items-center gap-1.5 bg-white border border-brand-200 rounded-full pl-2.5 pr-1.5 py-1"
          >
            <component :is="HeroIcons[grp.icon] || HeroIcons.StarIcon" class="w-3.5 h-3.5 text-brand-500 shrink-0" />
            <span class="text-sm font-medium text-brand-700">{{ grp.name }}</span>
            <span class="text-brand-300">·</span>
            <button
              v-for="sub in grp.subs"
              :key="sub.id"
              class="inline-flex items-center gap-1 bg-brand-500 text-white rounded-full pl-2 pr-1 py-0.5 text-xs font-medium cursor-pointer border-none hover:bg-brand-600 transition-colors"
              @click="toggleSel(sub)"
            >
              {{ sub.name }}
              <XMarkIcon class="w-3 h-3" />
            </button>
          </span>

          </div>

          <!-- Add topic / subtopic — pinned to the right, stays put -->
          <div ref="topicMenuRef" class="relative shrink-0">
            <button
              class="inline-flex items-center gap-1 border-2 border-dashed border-brand-400 text-brand-600 rounded-full px-3 py-1.5 text-sm font-medium cursor-pointer bg-white/60 hover:bg-brand-50 transition-colors whitespace-nowrap"
              @click="themeMenuOpen = !themeMenuOpen"
            >
              <PlusIcon class="w-4 h-4" />{{ t('search.addTheme') }}
              <ChevronDownIcon class="w-3.5 h-3.5" />
            </button>
            <div
              v-if="themeMenuOpen"
              class="absolute left-0 sm:left-auto sm:right-0 mt-2 z-30 bg-white rounded-xl shadow-lg border border-surface-200 py-1 w-72 max-w-[calc(100vw-2.5rem)] max-h-80 overflow-y-auto"
            >
            <div v-for="cat in categories" :key="cat.id">
              <div class="flex items-center">
                <button
                  class="flex items-center gap-2 flex-1 min-w-0 text-left px-3 py-2 text-sm cursor-pointer bg-transparent border-none hover:bg-surface-100"
                  :class="isSelected('cat', cat.id) ? 'text-brand-600 font-semibold' : 'text-surface-700'"
                  @click="toggleSel({ type: 'cat', id: cat.id, name: cat.name, icon: cat.icon })"
                >
                  <component :is="getCategoryIcon(cat)" class="w-4 h-4 text-brand-500 shrink-0" />
                  <span class="truncate">{{ cat.name }}</span>
                  <CheckIcon v-if="isSelected('cat', cat.id)" class="w-4 h-4 ml-auto shrink-0" />
                </button>
                <button
                  v-if="cat.subcategories?.length"
                  class="px-2 py-2 text-surface-400 hover:text-surface-700 cursor-pointer bg-transparent border-none shrink-0"
                  @click="expandedCat = expandedCat === cat.id ? null : cat.id"
                >
                  <ChevronDownIcon class="w-4 h-4 transition-transform" :class="{ 'rotate-180': expandedCat === cat.id }" />
                </button>
              </div>
              <div v-if="expandedCat === cat.id" class="pb-1">
                <button
                  v-for="sub in cat.subcategories"
                  :key="sub.id"
                  class="flex items-center gap-2 w-full text-left pl-9 pr-3 py-1.5 text-sm cursor-pointer bg-transparent border-none hover:bg-surface-100"
                  :class="isSelected('sub', sub.id) ? 'text-brand-600 font-semibold' : 'text-surface-600'"
                  @click="toggleSel({ type: 'sub', id: sub.id, name: sub.name, categoryId: cat.id })"
                >
                  <TagIcon class="w-3.5 h-3.5 text-surface-400 shrink-0" />
                  <span class="truncate">{{ sub.name }}</span>
                  <CheckIcon v-if="isSelected('sub', sub.id)" class="w-4 h-4 ml-auto shrink-0" />
                </button>
              </div>
            </div>
          </div>
          </div>
        </div>

        <!-- Optional: describe your situation to the AI -->
        <div class="mt-4">
          <button
            v-if="!aiOpen && !aiActive"
            class="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700 bg-transparent border-none cursor-pointer p-0"
            @click="aiOpen = true"
          >
            <SparklesIcon class="w-4 h-4" />{{ t('search.askAi') }}
          </button>

          <div v-else-if="aiOpen && !aiActive" class="flex items-end gap-2 max-w-xl">
            <textarea
              v-model="aiInput"
              rows="2"
              :placeholder="t('search.aiPlaceholder')"
              class="flex-1 resize-none text-sm border border-surface-300 rounded-xl px-3 py-2 outline-none focus:border-brand-400 transition-colors bg-white text-surface-800 placeholder-surface-400 leading-relaxed"
              @keydown.enter.prevent="runAi"
            />
            <button
              :disabled="!aiInput.trim() || aiLoading"
              class="w-9 h-9 bg-brand-500 hover:bg-brand-600 disabled:bg-surface-200 rounded-xl flex items-center justify-center transition-colors cursor-pointer border-none shrink-0"
              @click="runAi"
            >
              <PaperAirplaneIcon class="w-4 h-4 text-white" />
            </button>
            <button
              class="text-surface-400 hover:text-surface-600 bg-transparent border-none cursor-pointer p-1"
              @click="aiOpen = false"
            >
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Tabs -->
    <div class="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-surface-200">
      <div class="max-w-3xl mx-auto px-5 flex items-center gap-1 overflow-x-auto">
        <button
          v-for="tab in TABS"
          :key="tab"
          class="px-4 py-3 text-sm font-medium whitespace-nowrap border-none bg-transparent cursor-pointer border-b-2 transition-colors"
          :class="activeTab === tab
            ? 'text-brand-600 border-brand-500'
            : 'text-surface-500 border-transparent hover:text-surface-800'"
          @click="activeTab = tab"
        >
          {{ t(`search.tabs.${tab}`) }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <main class="max-w-3xl mx-auto px-5 py-6">
      <div v-if="loading || aiLoading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-500 rounded-full animate-spin" />
      </div>

      <template v-else>
        <!-- AI answer banner -->
        <div v-if="aiActive" class="bg-brand-50 border border-brand-200 rounded-2xl px-5 py-4 mb-5">
          <div class="flex items-start justify-between gap-3">
            <p class="flex items-start gap-2 text-surface-700 text-sm leading-relaxed">
              <SparklesIcon class="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
              <span>{{ aiReply }}</span>
            </p>
            <button
              class="flex items-center gap-1 text-xs font-medium text-surface-500 hover:text-surface-700 bg-transparent border-none cursor-pointer shrink-0 whitespace-nowrap"
              @click="clearAi"
            >
              {{ t('search.aiClear') }}<XMarkIcon class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <p v-if="!aiActive" class="text-sm text-surface-500 mb-4">{{ t('search.count', { n: results.length }) }}</p>

        <div v-if="!sections.length" class="bg-white rounded-2xl p-12 text-center shadow-sm border border-surface-100">
          <InboxIcon class="w-12 h-12 text-surface-300 mx-auto mb-3" />
          <p class="text-surface-400 text-sm">{{ t('search.empty') }}</p>
        </div>
        <ResourceList
          v-else
          :sections="sections"
          show-category
          :feedback-map="feedbackMap"
          :initial-resource-id="initialResourceId"
          @feedback-change="handleFeedbackChange"
        />
      </template>
    </main>
  </div>
</template>
