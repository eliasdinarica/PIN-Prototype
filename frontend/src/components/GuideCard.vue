<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  MapIcon, ChevronDownIcon, ShareIcon, BookmarkIcon,
  SparklesIcon, UsersIcon, ShieldCheckIcon,
} from '@heroicons/vue/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/vue/24/solid'
import ArticleRenderer from '@/components/ArticleRenderer.vue'
import { useSaved } from '@/composables/useSaved'

const { t } = useI18n()
const { isSaved, toggleSave } = useSaved()

const props = defineProps({
  guide: { type: Object, required: true },
  category: { type: Object, default: null },
  expanded: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const FLAGS = { en: '🇬🇧', fr: '🇫🇷', de: '🇩🇪', it: '🇮🇹', es: '🇪🇸', pt: '🇵🇹', ru: '🇷🇺', uk: '🇺🇦' }
const copied = ref(false)

// Saved guides are namespaced so their ids never clash with resource ids.
const savedKey = computed(() => `g:${props.guide.id}`)

// Per-guide language switch: re-fetch the guide so its step content swaps.
const currentLang = ref('fr')
const translated = ref(null)
const langOpen = ref(false)
const content = computed(() => translated.value || props.guide)

async function selectLang(lang) {
  langOpen.value = false
  if (lang === currentLang.value) return
  if (lang === 'fr') { translated.value = null; currentLang.value = 'fr'; return }
  try {
    const res = await fetch(`${API}/api/guides/${props.guide.id}/?lang=${lang}`)
    if (res.ok) { translated.value = await res.json(); currentLang.value = lang }
  } catch { /* keep current */ }
}

async function share() {
  const suffix = currentLang.value && currentLang.value !== 'fr' ? `?lang=${currentLang.value}` : ''
  const url = `${window.location.origin}/g/${props.guide.id}${suffix}`
  try {
    if (navigator.share) await navigator.share({ title: props.guide.title, url })
    else { await navigator.clipboard.writeText(url); copied.value = true; setTimeout(() => { copied.value = false }, 2000) }
  } catch { /* cancelled */ }
}
</script>

<template>
  <div :data-guide-id="guide.id" class="border-b border-surface-300/70">

    <!-- Collapsed row -->
    <button
      v-if="!expanded"
      class="flex items-center w-full py-4 text-left cursor-pointer bg-transparent border-none gap-4 group"
      @click="$emit('toggle', guide.id)"
    >
      <div class="flex-1 min-w-0">
        <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
        <h3 class="font-semibold text-lg leading-snug text-surface-800 group-hover:text-brand-500 transition-colors">
          {{ guide.title }}
        </h3>
      </div>
      <div class="flex items-center gap-3 shrink-0">
        <div class="flex flex-col items-end gap-0.5">
          <span v-if="guide.recommended_by_system" class="flex items-center gap-1 text-xs text-brand-500">
            <SparklesIcon class="w-3 h-3 shrink-0" />{{ t('community.bySystem') }}
          </span>
          <span v-if="guide.community_by_language" class="flex items-center gap-1 text-xs text-cyan-600">
            <UsersIcon class="w-3 h-3 shrink-0" />{{ t('community.byLanguage', { code: guide.community_by_language.toUpperCase() }) }}
          </span>
          <span v-if="guide.community_by_status" class="flex items-center gap-1 text-xs text-amber-600">
            <ShieldCheckIcon class="w-3 h-3 shrink-0" />{{ t('community.byStatus', { code: guide.community_by_status }) }}
          </span>
        </div>
        <span class="flex items-center gap-1 text-xs text-brand-500 bg-brand-50 px-2 py-0.5 rounded-full">
          <MapIcon class="w-3 h-3 shrink-0" />{{ t('nav.sections.pathways') }}
        </span>
        <ChevronDownIcon class="w-5 h-5 text-surface-400 shrink-0" />
      </div>
    </button>

    <!-- Expanded — title + action bar + description + steps -->
    <div v-else class="py-4 space-y-3">

      <div class="bg-white rounded-2xl px-6 py-5 shadow-sm">
        <button
          class="flex items-start w-full text-left cursor-pointer bg-transparent border-none gap-3"
          @click="$emit('toggle', guide.id)"
        >
          <div class="flex-1 min-w-0">
            <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
            <h3 class="font-bold text-xl leading-snug text-surface-800">{{ guide.title }}</h3>
            <span class="inline-flex items-center gap-1 text-xs text-brand-500 mt-1">
              <MapIcon class="w-3.5 h-3.5 shrink-0" />{{ t('pathways.steps', { n: guide.step_count }) }}
            </span>
            <div class="flex flex-col gap-0.5 mt-1">
              <span v-if="guide.recommended_by_system" class="flex items-center gap-1 text-xs text-brand-500">
                <SparklesIcon class="w-3 h-3 shrink-0" />{{ t('community.bySystem') }}
              </span>
              <span v-if="guide.community_by_language" class="flex items-center gap-1 text-xs text-cyan-600">
                <UsersIcon class="w-3 h-3 shrink-0" />{{ t('community.byLanguage', { code: guide.community_by_language.toUpperCase() }) }}
              </span>
              <span v-if="guide.community_by_status" class="flex items-center gap-1 text-xs text-amber-600">
                <ShieldCheckIcon class="w-3 h-3 shrink-0" />{{ t('community.byStatus', { code: guide.community_by_status }) }}
              </span>
            </div>
          </div>
          <ChevronDownIcon class="w-5 h-5 text-brand-500 shrink-0 rotate-180 mt-1" />
        </button>

        <!-- Action bar: save / share / language (identical to resources) -->
        <div class="flex items-center justify-between gap-3 border-y border-surface-100 py-2.5 my-4">
          <div class="flex items-center gap-1">
            <button
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
              :class="isSaved(savedKey) ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
              @click.stop="toggleSave(savedKey)"
            >
              <component :is="isSaved(savedKey) ? BookmarkSolidIcon : BookmarkIcon" class="w-5 h-5" />
              {{ isSaved(savedKey) ? t('actions.saved') : t('actions.save') }}
            </button>
            <button
              class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none text-surface-500 hover:text-brand-600"
              @click.stop="share"
            >
              <ShareIcon class="w-5 h-5" />
              {{ copied ? t('actions.copied') : t('actions.share') }}
            </button>
          </div>
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
                v-for="lang in (guide.languages || ['fr'])"
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

        <p v-if="content.description" class="text-surface-700 text-[15px] leading-relaxed">
          {{ content.description }}
        </p>
      </div>

      <!-- Steps timeline -->
      <div
        v-for="(step, idx) in content.steps"
        :key="step.id"
        class="flex gap-4"
      >
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
            {{ idx + 1 }}
          </div>
          <div v-if="idx < content.steps.length - 1" class="w-px flex-1 bg-surface-300 mt-2" />
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
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
