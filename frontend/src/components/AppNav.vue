<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { BookOpenIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <!-- Discreet banner pinned to the bottom-left -->
  <aside class="fixed left-0 bottom-6 z-50">
    <button
      class="flex items-center gap-2.5 w-56 bg-white border border-l-0 border-surface-200 shadow-lg rounded-r-2xl pl-3 pr-3.5 py-3 cursor-pointer text-left transition-shadow duration-200 hover:shadow-xl"
      :aria-label="t('nav.questionnaire')"
      @click="router.push('/profile')"
    >
      <span class="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
        <BookOpenIcon class="w-5 h-5 text-brand-500" />
      </span>
      <span class="min-w-0">
        <span class="block text-sm font-semibold text-surface-800 leading-tight">{{ t('nav.questionnaire') }}</span>
        <span class="block text-xs text-surface-500 leading-snug">{{ t('nav.surveyHint') }}</span>
      </span>
    </button>
  </aside>
</template>
