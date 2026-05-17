<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { UserCircleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <div class="fixed bottom-6 left-4 z-50">
    <button
      class="flex items-center gap-2 bg-surface-800 shadow-md rounded-xl pl-3 pr-4 py-2 text-sm font-medium text-white hover:bg-surface-700 border border-surface-700 transition-all duration-150 cursor-pointer"
      @click="router.push('/')"
    >
      <UserCircleIcon class="w-5 h-5" />
      <span>{{ t('nav.editProfile') }}</span>
    </button>
  </div>
</template>
