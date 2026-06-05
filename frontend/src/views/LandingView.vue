<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  SparklesIcon, MagnifyingGlassIcon,
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
  <div class="min-h-screen bg-surface-900 flex flex-col">

    <!-- ── Hero ──────────────────────────────────────── -->
    <header class="max-w-3xl w-full mx-auto px-5 pt-16 pb-10">
      <p class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-400 mb-6">
        Immiguide
      </p>
      <h1 class="text-4xl sm:text-5xl font-bold text-white leading-[1.05] mb-4">
        {{ t('landing.headline') }}
      </h1>
      <p class="text-surface-300 text-lg leading-relaxed max-w-md">
        {{ t('landing.heroSub') }}
      </p>
    </header>

    <main class="max-w-3xl w-full mx-auto px-5 pb-16 flex-1 flex flex-col">

      <!-- ── Schéma : comment marche la recommandation (juste au-dessus du questionnaire) ── -->
      <p class="text-xs font-semibold uppercase tracking-widest text-surface-400 mb-8 text-center">
        {{ t('landing.how.title') }}
      </p>
      <div class="flex flex-col sm:flex-row items-stretch justify-center gap-3 sm:gap-2 mb-6">
        <template v-for="(step, i) in steps" :key="i">
          <div class="flex-1 flex flex-col items-center text-center bg-surface-800 border border-surface-700 rounded-2xl px-5 py-6">
            <div class="w-12 h-12 rounded-full bg-brand-500/10 flex items-center justify-center mb-3">
              <component :is="step.icon" class="w-6 h-6 text-brand-400" />
            </div>
            <p class="text-white text-sm font-semibold leading-snug mb-1">{{ step.title }}</p>
            <p class="text-surface-400 text-xs leading-relaxed">{{ step.desc }}</p>
          </div>
          <div
            v-if="i < steps.length - 1"
            class="flex items-center justify-center shrink-0"
          >
            <ArrowRightIcon class="w-5 h-5 text-surface-500 rotate-90 sm:rotate-0" />
          </div>
        </template>
      </div>

      <!-- Note : likes + recommandations communautaires -->
      <p class="flex items-start gap-2 text-surface-400 text-xs leading-relaxed max-w-md mx-auto text-center justify-center mb-16">
        <HandThumbUpIcon class="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
        <span>{{ t('landing.how.note') }}</span>
      </p>

      <!-- ── Point d'entrée : titre + deux cercles ── -->
      <p class="text-white font-semibold text-lg text-center mb-8">
        {{ t('landing.q.tag') }}
      </p>
      <div class="flex items-center justify-center gap-8 sm:gap-14 flex-wrap">

        <div class="flex flex-col items-center gap-3">
          <button
            class="w-36 h-36 sm:w-44 sm:h-44 rounded-full bg-brand-500 hover:bg-brand-600 active:bg-brand-700 flex flex-col items-center justify-center gap-2.5 transition-all duration-150 cursor-pointer border-none shadow-lg hover:scale-105"
            @click="router.push('/profile')"
          >
            <SparklesIcon class="w-7 h-7 sm:w-8 sm:h-8 text-white" />
            <span class="text-white font-semibold text-xs sm:text-sm text-center leading-snug px-5">
              {{ t('landing.q.cta') }}
            </span>
          </button>
          <p class="text-surface-400 text-xs text-center max-w-[140px] leading-snug">
            {{ t('landing.q.ctaDesc') }}
          </p>
        </div>

        <div class="flex flex-col items-center gap-3">
          <button
            class="w-36 h-36 sm:w-44 sm:h-44 rounded-full bg-transparent border-2 border-surface-600 hover:border-brand-400 flex flex-col items-center justify-center gap-2.5 transition-all duration-150 cursor-pointer group hover:scale-105"
            @click="router.push('/hub')"
          >
            <MagnifyingGlassIcon class="w-7 h-7 sm:w-8 sm:h-8 text-surface-400 group-hover:text-brand-400 transition-colors" />
            <span class="text-surface-300 group-hover:text-white font-semibold text-xs sm:text-sm text-center leading-snug px-5 transition-colors">
              {{ t('landing.q.ctaExplore') }}
            </span>
          </button>
          <p class="text-surface-500 text-xs text-center max-w-[140px] leading-snug">
            {{ t('landing.q.exploreDesc') }}
          </p>
        </div>

      </div>

      <p class="text-surface-600 text-xs text-center mt-10">{{ t('landing.q.privacy') }}</p>

    </main>

  </div>
</template>
