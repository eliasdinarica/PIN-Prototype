<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDownIcon, GlobeAltIcon } from '@heroicons/vue/24/outline'

const { locale } = useI18n()

// Interface language switch. Mirrors the per-resource language button, but
// drives the whole UI (vue-i18n) instead of a single resource's content.
const UI_LANGUAGES = [
  { code: 'en', flag: '🇬🇧' },
  { code: 'fr', flag: '🇫🇷' },
  { code: 'uk', flag: '🇺🇦' },
  { code: 'ru', flag: '🇷🇺' },
]
const FLAGS = Object.fromEntries(UI_LANGUAGES.map(l => [l.code, l.flag]))

const open = ref(false)
const rootRef = ref(null)

function select(code) {
  open.value = false
  locale.value = code
  localStorage.setItem('profileLanguage', code)
}

function onDocClick(e) {
  if (open.value && rootRef.value && !rootRef.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))
</script>

<template>
  <div ref="rootRef" class="fixed top-3 right-3 z-[1200]">
    <button
      class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium text-surface-600 hover:text-brand-600 bg-white border border-surface-200 shadow-sm cursor-pointer"
      @click="open = !open"
    >
      <GlobeAltIcon class="w-4 h-4 text-surface-400" />
      <span>{{ FLAGS[locale] || '🌐' }}</span>
      <span>{{ String(locale).toUpperCase() }}</span>
      <ChevronDownIcon class="w-3.5 h-3.5 text-surface-400" />
    </button>
    <div
      v-if="open"
      class="absolute right-0 mt-1 z-10 bg-white rounded-lg shadow-lg border border-surface-200 py-1 min-w-28"
    >
      <button
        v-for="lang in UI_LANGUAGES"
        :key="lang.code"
        class="flex items-center gap-2 w-full text-left px-3 py-1.5 text-sm cursor-pointer bg-transparent border-none hover:bg-surface-100"
        :class="lang.code === locale ? 'text-brand-600 font-semibold' : 'text-surface-600'"
        @click="select(lang.code)"
      >
        <span>{{ lang.flag }}</span><span>{{ lang.code.toUpperCase() }}</span>
      </button>
    </div>
  </div>
</template>
