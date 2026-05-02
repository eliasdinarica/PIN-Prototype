<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { UserCircleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <div class="fixed top-4 right-4 z-50">
    <button
      class="flex items-center gap-2 bg-white shadow-md rounded-full pl-3 pr-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 border border-indigo-100 transition-all duration-150 cursor-pointer"
      @click="router.push('/')"
    >
      <UserCircleIcon class="w-5 h-5" />
      <span>{{ t('nav.editProfile') }}</span>
    </button>
  </div>
</template>
