<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  SparklesIcon, UsersIcon, ShieldCheckIcon, ArrowDownTrayIcon, DocumentTextIcon,
  ChevronDownIcon, HandThumbUpIcon, HandThumbDownIcon, ShareIcon, BookmarkIcon,
  SpeakerWaveIcon, StopCircleIcon,
} from '@heroicons/vue/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/vue/24/solid'
import ArticleRenderer from '@/components/ArticleRenderer.vue'
import ResourceLocation from '@/components/ResourceLocation.vue'
import { useSaved } from '@/composables/useSaved'
import { useSpeech } from '@/composables/useSpeech'

const { t } = useI18n()
const { isSaved, toggleSave } = useSaved()
const { supported: speechSupported, speakingId, toggle: toggleSpeech } = useSpeech()

// Speech id + text for the opening section (title + description).
const introId = computed(() => `r${props.resource.id}-intro`)
const introText = computed(() => [content.value.name, content.value.description].filter(Boolean).join('. '))

const props = defineProps({
  resource: { type: Object, required: true },
  category: { type: Object, default: null },
  feedback: { type: Object, default: null },
  expanded: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'feedback-change'])

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const FLAGS = { en: '🇬🇧', fr: '🇫🇷', de: '🇩🇪', it: '🇮🇹', es: '🇪🇸', pt: '🇵🇹', ru: '🇷🇺', uk: '🇺🇦' }
const copied = ref(false)

// Per-resource language switch: base content vs. a fetched translation.
const currentLang = ref('fr')
const translated = ref(null)
const langOpen = ref(false)
const content = computed(() => translated.value || props.resource)

async function selectLang(lang) {
  langOpen.value = false
  if (lang === currentLang.value) return
  if (lang === 'fr') { translated.value = null; currentLang.value = 'fr'; return }
  try {
    const res = await fetch(`${API}/api/resources/${props.resource.id}/?lang=${lang}`)
    if (res.ok) { translated.value = await res.json(); currentLang.value = lang }
  } catch { /* keep current */ }
}

// When structured places exist, the Location section is rendered separately.
const displaySections = computed(() => {
  const s = content.value.sections || []
  return content.value.places?.length ? s.filter(x => x.key !== 'location') : s
})

function onFeedback(isUseful) {
  if (props.feedback?.is_useful === isUseful) {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback.id, isUseful: null })
  } else {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback?.id ?? null, isUseful })
  }
}

async function share() {
  // Keep the language currently being viewed in the shared link.
  const suffix = currentLang.value && currentLang.value !== 'fr' ? `?lang=${currentLang.value}` : ''
  const url = `${window.location.origin}/r/${props.resource.id}${suffix}`
  try {
    if (navigator.share) {
      await navigator.share({ title: props.resource.name, url })
    } else {
      await navigator.clipboard.writeText(url)
      copied.value = true
      setTimeout(() => { copied.value = false }, 2000)
    }
  } catch { /* user cancelled share */ }
}

function filenameFromUrl(url) {
  try { return decodeURIComponent(url.split('/').pop().split('?')[0]) } catch { return url }
}
</script>

<template>
  <div :data-resource-id="resource.id" class="border-b border-surface-300/70">

    <!-- Collapsed row -->
    <button
      v-if="!expanded"
      class="flex flex-col w-full py-4 text-left cursor-pointer bg-transparent border-none gap-1.5 group"
      @click="$emit('toggle', resource.id)"
    >
      <div class="flex items-center w-full gap-3">
        <div class="flex-1 min-w-0">
          <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
          <h3 class="font-semibold text-lg leading-snug text-surface-800 group-hover:text-brand-500 transition-colors">
            {{ resource.name }}
          </h3>
        </div>
        <ChevronDownIcon class="w-5 h-5 text-surface-400 shrink-0" />
      </div>
      <div
        v-if="resource.recommended_by_system || resource.recommended_by_similar || resource.recommended_by_affinity"
        class="flex flex-wrap justify-end gap-x-3 gap-y-0.5"
      >
        <span v-if="resource.recommended_by_system" class="flex items-center gap-1 text-xs text-brand-500">
          <SparklesIcon class="w-3 h-3 shrink-0" />{{ t('community.bySystem') }}
        </span>
        <span v-if="resource.recommended_by_similar" class="flex items-center gap-1 text-xs text-cyan-600">
          <UsersIcon class="w-3 h-3 shrink-0" />{{ t('community.bySimilar') }}
        </span>
        <span v-if="resource.recommended_by_affinity" class="flex items-center gap-1 text-xs text-violet-600">
          <ShieldCheckIcon class="w-3 h-3 shrink-0" />{{ t('community.byAffinity') }}
        </span>
      </div>
    </button>

    <!-- Expanded — everything in cards, title inside the first bubble -->
    <div v-else class="py-4 space-y-3">

      <!-- First bubble: title + action bar + description -->
      <div class="bg-white rounded-2xl px-6 py-5 shadow-sm">

        <!-- Title row (click to close) -->
        <button
          class="flex items-start w-full text-left cursor-pointer bg-transparent border-none gap-3"
          @click="$emit('toggle', resource.id)"
        >
          <div class="flex-1 min-w-0">
            <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
            <h3 class="font-bold text-xl leading-snug text-surface-800">{{ content.name }}</h3>
            <p v-if="resource.author" class="text-xs text-surface-400 mt-0.5">{{ t('resource.writtenBy', { name: resource.author }) }}</p>
            <div class="flex flex-col gap-0.5 mt-1">
              <span v-if="resource.recommended_by_system" class="flex items-center gap-1 text-xs text-brand-500">
                <SparklesIcon class="w-3 h-3 shrink-0" />{{ t('community.bySystem') }}
              </span>
              <span v-if="resource.recommended_by_similar" class="flex items-center gap-1 text-xs text-cyan-600">
                <UsersIcon class="w-3 h-3 shrink-0" />{{ t('community.bySimilar') }}
              </span>
              <span v-if="resource.recommended_by_affinity" class="flex items-center gap-1 text-xs text-violet-600">
                <ShieldCheckIcon class="w-3 h-3 shrink-0" />{{ t('community.byAffinity') }}
              </span>
            </div>
          </div>
          <ChevronDownIcon class="w-5 h-5 text-brand-500 shrink-0 rotate-180 mt-1" />
        </button>

        <!-- Action bar: save / share / language -->
        <div class="flex items-center justify-between gap-3 border-y border-surface-100 py-2.5 my-4">
          <div class="flex items-center gap-1">
            <button
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
              :class="isSaved(resource.id) ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
              @click.stop="toggleSave(resource.id)"
            >
              <component :is="isSaved(resource.id) ? BookmarkSolidIcon : BookmarkIcon" class="w-5 h-5" />
              {{ isSaved(resource.id) ? t('actions.saved') : t('actions.save') }}
            </button>
            <button
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none text-surface-500 hover:text-brand-600"
              @click.stop="share"
            >
              <ShareIcon class="w-5 h-5" />
              {{ copied ? t('actions.copied') : t('actions.share') }}
            </button>
            <button
              v-if="speechSupported && introText"
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
              :class="speakingId === introId ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
              @click.stop="toggleSpeech(introId, introText, currentLang)"
            >
              <component :is="speakingId === introId ? StopCircleIcon : SpeakerWaveIcon" class="w-5 h-5" />
              {{ speakingId === introId ? t('actions.stopListen') : t('actions.listen') }}
            </button>
          </div>
          <!-- Language switch -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium text-surface-600 hover:text-brand-600 bg-transparent border-none cursor-pointer"
              @click.stop="langOpen = !langOpen"
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
                v-for="lang in (resource.languages || ['fr'])"
                :key="lang"
                class="flex items-center gap-2 w-full text-left px-3 py-1.5 text-sm cursor-pointer bg-transparent border-none hover:bg-surface-100"
                :class="lang === currentLang ? 'text-brand-600 font-semibold' : 'text-surface-600'"
                @click.stop="selectLang(lang)"
              >
                <span>{{ FLAGS[lang] }}</span><span>{{ lang.toUpperCase() }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Description -->
        <p v-if="content.description" class="text-surface-700 text-[15px] leading-relaxed">
          {{ content.description }}
        </p>
      </div>

      <!-- Section cards (Why / How) -->
      <ArticleRenderer
        v-if="displaySections.length"
        :sections="displaySections"
        :lang="currentLang"
        :prefix="`r${resource.id}-`"
      />

      <!-- Location: structured places + map -->
      <ResourceLocation v-if="content.places?.length" :places="content.places" :lang="currentLang" />

      <!-- Attachments -->
      <div v-if="resource.attachments?.length" class="bg-white rounded-2xl px-6 py-5 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Fichiers</p>
        <div class="space-y-2">
          <a
            v-for="a in resource.attachments"
            :key="a.id"
            :href="a.file"
            target="_blank"
            download
            class="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:border-brand-400 hover:bg-brand-50 transition-colors no-underline"
          >
            <DocumentTextIcon class="w-5 h-5 text-brand-500 shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-800 text-sm truncate">{{ a.label || filenameFromUrl(a.file) }}</p>
              <p v-if="a.label" class="text-xs text-gray-400 truncate">{{ filenameFromUrl(a.file) }}</p>
            </div>
            <ArrowDownTrayIcon class="w-4 h-4 text-gray-400 shrink-0" />
          </a>
        </div>
      </div>

      <!-- Sticky feedback — review the open resource while reading -->
      <div class="sticky bottom-3 z-[1100] pt-1">
        <div class="bg-white rounded-2xl shadow-lg border border-surface-200 px-5 py-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p class="flex items-center gap-2 text-surface-800 font-semibold text-sm">
            {{ t('feedback.useful') }}
          </p>
          <div class="flex items-center gap-2">
            <button
              class="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl border-2 text-sm font-semibold transition-colors cursor-pointer flex-1 sm:flex-none"
              :class="feedback?.is_useful === true
                ? 'bg-brand-500 border-brand-500 text-white'
                : 'bg-white border-brand-500 text-brand-600 hover:bg-brand-50'"
              @click="onFeedback(true)"
            >
              <HandThumbUpIcon class="w-4 h-4" />{{ t('feedback.yes') }}
            </button>
            <button
              class="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl border-2 text-sm font-semibold transition-colors cursor-pointer flex-1 sm:flex-none"
              :class="feedback?.is_useful === false
                ? 'bg-brand-500 border-brand-500 text-white'
                : 'bg-white border-brand-500 text-brand-600 hover:bg-brand-50'"
              @click="onFeedback(false)"
            >
              <HandThumbDownIcon class="w-4 h-4" />{{ t('feedback.no') }}
            </button>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>
