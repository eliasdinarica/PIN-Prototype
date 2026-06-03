<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { BookOpenIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <div class="fixed top-5 right-5 z-50">
    <button
      class="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 active:bg-brand-700 text-white px-4 py-2.5 rounded-full shadow-lg transition-all duration-150 cursor-pointer border-none"
      @click="router.push('/profile')"
    >
      <BookOpenIcon class="w-4 h-4 shrink-0" />
      <span class="text-sm font-semibold">{{ t('nav.questionnaire') }}</span>
    </button>
  </div>
</template>
