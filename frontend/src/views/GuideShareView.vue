<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ShareIcon, BookmarkIcon, ChevronDownIcon, MapIcon, SpeakerWaveIcon, StopCircleIcon } from '@heroicons/vue/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/vue/24/solid'
import ArticleRenderer from '@/components/ArticleRenderer.vue'
import { useSaved } from '@/composables/useSaved'
import { useSpeech } from '@/composables/useSpeech'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isSaved, toggleSave } = useSaved()
const { supported: speechSupported, speakingId, toggle: toggleSpeech } = useSpeech()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const guide = ref(null)
const loading = ref(true)
const notFound = ref(false)
const copied = ref(false)

const FLAGS = { en: '🇬🇧', fr: '🇫🇷', de: '🇩🇪', it: '🇮🇹', es: '🇪🇸', pt: '🇵🇹', ru: '🇷🇺', uk: '🇺🇦' }
const currentLang = ref('fr')
const langOpen = ref(false)

const savedKey = `g:${route.params.id}`

const introId = computed(() => `g${route.params.id}-intro`)
const introText = computed(() => [guide.value?.title, guide.value?.description].filter(Boolean).join('. '))

async function selectLang(lang) {
  langOpen.value = false
  if (lang === currentLang.value) return
  const url = lang === 'fr'
    ? `${API}/api/guides/${route.params.id}/`
    : `${API}/api/guides/${route.params.id}/?lang=${lang}`
  try {
    const res = await fetch(url)
    if (res.ok) { guide.value = await res.json(); currentLang.value = lang }
  } catch { /* keep current */ }
}

async function share() {
  const suffix = currentLang.value && currentLang.value !== 'fr' ? `?lang=${currentLang.value}` : ''
  const url = `${window.location.origin}/g/${route.params.id}${suffix}`
  try {
    if (navigator.share) await navigator.share({ title: guide.value?.title, url })
    else { await navigator.clipboard.writeText(url); copied.value = true; setTimeout(() => { copied.value = false }, 2000) }
  } catch { /* cancelled */ }
}

onMounted(async () => {
  const wanted = route.query.lang
  const url = wanted && wanted !== 'fr'
    ? `${API}/api/guides/${route.params.id}/?lang=${wanted}`
    : `${API}/api/guides/${route.params.id}/`
  try {
    const res = await fetch(url)
    if (!res.ok) { notFound.value = true; return }
    guide.value = await res.json()
    if (wanted && (guide.value.languages || []).includes(wanted)) currentLang.value = wanted
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <header class="border-b border-surface-200/70 bg-white/60 backdrop-blur">
      <div class="max-w-2xl mx-auto px-5 py-3">
        <button
          class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-500 bg-transparent border-none cursor-pointer p-0"
          @click="router.push('/')"
        >
          Immiguide
        </button>
      </div>
    </header>

    <main class="max-w-2xl mx-auto px-5 py-8">

      <div v-if="loading" class="flex justify-center py-32">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-500 rounded-full animate-spin" />
      </div>

      <p v-else-if="notFound" class="text-center text-surface-500 py-32">404 — guide not found.</p>

      <template v-else-if="guide">
        <div class="space-y-3">

          <!-- Title + action bar + description -->
          <div class="bg-white rounded-2xl px-6 py-5 shadow-sm">
            <h1 class="font-bold text-2xl leading-snug text-surface-800">{{ guide.title }}</h1>
            <span class="inline-flex items-center gap-1 text-xs text-brand-500 mt-1">
              <MapIcon class="w-3.5 h-3.5 shrink-0" />{{ t('pathways.steps', { n: guide.step_count }) }}
            </span>

            <div class="flex items-center justify-between gap-3 border-y border-surface-100 py-2.5 my-4">
              <div class="flex items-center gap-1">
                <button
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
                  :class="isSaved(savedKey) ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
                  @click="toggleSave(savedKey)"
                >
                  <component :is="isSaved(savedKey) ? BookmarkSolidIcon : BookmarkIcon" class="w-5 h-5" />
                  {{ isSaved(savedKey) ? t('actions.saved') : t('actions.save') }}
                </button>
                <button
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none text-surface-500 hover:text-brand-600"
                  @click="share"
                >
                  <ShareIcon class="w-5 h-5" />
                  {{ copied ? t('actions.copied') : t('actions.share') }}
                </button>
                <button
                  v-if="speechSupported && introText"
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
                  :class="speakingId === introId ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
                  @click="toggleSpeech(introId, introText, currentLang)"
                >
                  <component :is="speakingId === introId ? StopCircleIcon : SpeakerWaveIcon" class="w-5 h-5" />
                  {{ speakingId === introId ? t('actions.stopListen') : t('actions.listen') }}
                </button>
              </div>
              <div class="relative">
                <button
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium text-surface-600 hover:text-brand-600 bg-transparent border-none cursor-pointer"
                  @click="langOpen = !langOpen"
                >
                  <span>{{ FLAGS[currentLang] }}</span>
                  <span>{{ currentLang.toUpperCase() }}</span>
                  <ChevronDownIcon class="w-3.5 h-3.5 text-surface-400" />
                </button>
                <div
                  v-if="langOpen"
                  class="absolute right-0 mt-1 z-20 bg-white rounded-lg shadow-lg border border-surface-200 py-1 min-w-28"
                >
                  <button
                    v-for="lang in (guide.languages || ['fr'])"
                    :key="lang"
                    class="flex items-center gap-2 w-full text-left px-3 py-1.5 text-sm cursor-pointer bg-transparent border-none hover:bg-surface-100"
                    :class="lang === currentLang ? 'text-brand-600 font-semibold' : 'text-surface-600'"
                    @click="selectLang(lang)"
                  >
                    <span>{{ FLAGS[lang] }}</span><span>{{ lang.toUpperCase() }}</span>
                  </button>
                </div>
              </div>
            </div>

            <p v-if="guide.description" class="text-surface-700 text-[15px] leading-relaxed">
              {{ guide.description }}
            </p>
          </div>

          <!-- Steps timeline -->
          <div
            v-for="(step, idx) in guide.steps"
            :key="step.id"
            class="flex gap-4"
          >
            <div class="flex flex-col items-center">
              <div class="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
                {{ idx + 1 }}
              </div>
              <div v-if="idx < guide.steps.length - 1" class="w-px flex-1 bg-surface-300 mt-2" />
            </div>
            <div class="flex-1 min-w-0 pb-2">
              <div class="bg-white rounded-2xl p-5 shadow-sm border border-surface-200/60">
                <h4 class="font-bold text-surface-800 text-lg leading-snug mb-1">
                  {{ step.step_label || step.resource.name }}
                </h4>
                <p v-if="step.resource.description" class="text-surface-500 text-sm leading-relaxed mb-3">
                  {{ step.resource.description }}
                </p>
                <ArticleRenderer
                  v-if="step.resource.sections?.length"
                  :sections="step.resource.sections"
                  :lang="currentLang"
                  :prefix="`g${route.params.id}-s${step.id}-`"
                />
              </div>
            </div>
          </div>
        </div>
      </template>

    </main>
  </div>
</template>
