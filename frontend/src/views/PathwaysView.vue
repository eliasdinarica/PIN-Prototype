<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const pathways = ref([])
const loading = ref(true)

function getIcon(name) {
  return HeroIcons[name] || HeroIcons.MapIcon
}

onMounted(async () => {
  const res = await fetch(`${API}/api/pathways/`)
  pathways.value = await res.json()
  loading.value = false
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200 flex flex-col">

    <header class="px-5 pt-10 pb-6 max-w-xl mx-auto w-full">
      <button
        class="flex items-center gap-1 text-xs text-surface-500 hover:text-surface-700 mb-5 cursor-pointer bg-transparent border-none p-0 transition-colors"
        @click="router.push('/hub')"
      >
        <ArrowLeftIcon class="w-3.5 h-3.5" />Hub
      </button>
      <p class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-500 mb-3">{{ t('pathways.eyebrow') }}</p>
      <h1 class="text-2xl sm:text-3xl font-bold text-surface-800 leading-snug">{{ t('pathways.title') }}</h1>
      <p class="text-surface-500 text-sm mt-1.5 leading-relaxed">{{ t('pathways.subtitle') }}</p>
    </header>

    <main class="flex-1 px-5 pb-16 max-w-xl mx-auto w-full">

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-500 rounded-full animate-spin" />
      </div>

      <p v-else-if="!pathways.length" class="text-surface-400 text-sm text-center py-20">
        {{ t('pathways.empty') }}
      </p>

      <div v-else class="flex flex-col gap-3">
        <button
          v-for="p in pathways"
          :key="p.id"
          class="group w-full text-left bg-white border border-surface-200 shadow-sm rounded-2xl p-5 hover:border-brand-500/40 hover:shadow-md transition-all cursor-pointer"
          @click="router.push(`/pathways/${p.id}`)"
        >
          <div class="flex items-center gap-4">
            <div class="w-11 h-11 rounded-xl bg-brand-500/10 flex items-center justify-center shrink-0">
              <component :is="getIcon(p.icon)" class="w-6 h-6 text-brand-500" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-0.5">
                <h2 class="text-surface-800 font-semibold text-base leading-snug">{{ p.title }}</h2>
                <span class="text-xs bg-surface-100 text-surface-500 px-2 py-0.5 rounded-full shrink-0">
                  {{ t('pathways.steps', { n: p.step_count }) }}
                </span>
              </div>
              <p class="text-surface-500 text-sm leading-snug line-clamp-2">{{ p.description }}</p>
            </div>
            <ArrowRightIcon class="w-5 h-5 text-surface-400 group-hover:text-brand-500 group-hover:translate-x-0.5 transition-all shrink-0" />
          </div>
        </button>
      </div>

    </main>
  </div>
</template>
