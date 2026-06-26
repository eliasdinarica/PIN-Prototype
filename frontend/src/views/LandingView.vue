<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  MagnifyingGlassIcon,
  ClipboardDocumentListIcon, AdjustmentsHorizontalIcon,
  ArrowRightIcon, HandThumbUpIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()

const steps = computed(() => [
  { icon: ClipboardDocumentListIcon, title: t('landing.how.s1title'), desc: t('landing.how.s1desc') },
  { icon: AdjustmentsHorizontalIcon, title: t('landing.how.s2title'), desc: t('landing.how.s2desc') },
])
</script>

<template>
  <div class="min-h-screen bg-surface-500 flex flex-col">

    <!-- ── Hero ──────────────────────────────────────── -->
    <header class="max-w-3xl w-full mx-auto px-5 pt-8 pb-5">
      <p class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-400 mb-3">
        Immiguide
      </p>
      <h1 class="text-3xl sm:text-4xl font-bold text-white leading-[1.05] mb-3">
        {{ t('landing.headline') }}
      </h1>
      <p class="text-surface-300 text-base leading-relaxed max-w-md">
        {{ t('landing.heroSub') }}
      </p>
    </header>

    <main class="max-w-3xl w-full mx-auto px-5 pb-8 flex-1 flex flex-col">

      <!-- ── Point d'entrée : titre + deux cercles ── -->
      <p class="text-white font-semibold text-lg text-center mb-5">
        {{ t('landing.q.tag') }}
      </p>
      <div class="flex items-center justify-center gap-6 sm:gap-10 flex-wrap">

        <div class="flex flex-col items-center gap-2.5">
          <button
            class="w-28 h-28 sm:w-36 sm:h-36 rounded-full bg-brand-500 hover:bg-brand-600 active:bg-brand-700 flex flex-col items-center justify-center gap-2 transition-all duration-150 cursor-pointer border-none shadow-lg hover:scale-105"
            @click="router.push('/profile')"
          >
            <ClipboardDocumentListIcon class="w-6 h-6 sm:w-7 sm:h-7 text-white" />
            <span class="text-white font-semibold text-xs sm:text-sm text-center leading-snug px-4">
              {{ t('landing.q.cta') }}
            </span>
          </button>
          <p class="text-surface-200 text-xs text-center max-w-[140px] leading-snug">
            {{ t('landing.q.ctaDesc') }}
          </p>
        </div>

        <div class="flex flex-col items-center gap-2.5">
          <button
            class="w-28 h-28 sm:w-36 sm:h-36 rounded-full bg-transparent border-2 border-surface-300 hover:border-brand-400 flex flex-col items-center justify-center gap-2 transition-all duration-150 cursor-pointer group hover:scale-105"
            @click="router.push('/hub')"
          >
            <MagnifyingGlassIcon class="w-6 h-6 sm:w-7 sm:h-7 text-surface-200 group-hover:text-brand-400 transition-colors" />
            <span class="text-surface-100 group-hover:text-white font-semibold text-xs sm:text-sm text-center leading-snug px-4 transition-colors">
              {{ t('landing.q.ctaExplore') }}
            </span>
          </button>
          <p class="text-surface-200 text-xs text-center max-w-[140px] leading-snug">
            {{ t('landing.q.exploreDesc') }}
          </p>
        </div>

      </div>

      <p class="text-surface-300 text-xs text-center mt-5 mb-10">{{ t('landing.q.privacy') }}</p>

      <!-- ── Schéma informatif : comment marche la recommandation ── -->
      <p class="text-xs font-semibold uppercase tracking-widest text-surface-200 mb-4 text-center">
        {{ t('landing.how.title') }}
      </p>
      <div class="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 mb-4">
        <template v-for="(step, i) in steps" :key="i">
          <div class="flex-1 flex flex-col items-center text-center px-2 py-1">
            <div class="w-12 h-12 rounded-full bg-brand-500/15 flex items-center justify-center mb-2">
              <component :is="step.icon" class="w-6 h-6 text-brand-300" />
            </div>
            <p class="text-white text-sm font-semibold leading-snug mb-1">{{ step.title }}</p>
            <p class="text-surface-200 text-xs leading-relaxed max-w-[180px]">{{ step.desc }}</p>
          </div>
          <div
            v-if="i < steps.length - 1"
            class="flex items-center justify-center shrink-0 text-surface-200"
          >
            <ArrowRightIcon class="w-6 h-6 rotate-90 sm:rotate-0" />
          </div>
        </template>
      </div>

      <!-- Note : likes + recommandations communautaires -->
      <p class="flex items-start gap-2 text-surface-200 text-xs leading-relaxed max-w-md mx-auto text-center justify-center">
        <HandThumbUpIcon class="w-4 h-4 text-brand-300 shrink-0 mt-0.5" />
        <span>{{ t('landing.how.note') }}</span>
      </p>

    </main>

  </div>
</template>
