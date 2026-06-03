<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { SparklesIcon, MagnifyingGlassIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()

const hasProfile = ref(false)
onMounted(() => { hasProfile.value = !!localStorage.getItem('profileId') })

const topics = ['work', 'permit', 'french', 'housing', 'health', 'family', 'banking', 'rights']

const exTitles = computed(() => t('landing.exTitles').split('|'))
const exDescs   = computed(() => t('landing.exDescs').split('|'))
const exCats    = computed(() => t('landing.exCats').split('|'))
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

    <!-- ── Section unique : sujets → ressources → questionnaire ── -->
    <section class="border-t border-surface-700 flex-1 bg-surface-800">
      <div class="max-w-3xl w-full mx-auto px-5 py-12">

        <!-- "Si vous avez besoin de..." + tags -->
        <p class="text-xs font-semibold uppercase tracking-widest text-surface-400 mb-4">
          {{ t('landing.needLabel') }}
        </p>
        <div class="flex flex-wrap gap-2 mb-3">
          <span
            v-for="key in topics"
            :key="key"
            class="px-3 py-1.5 rounded-full border border-surface-600 text-surface-200 text-sm"
          >{{ t(`landing.topics.${key}`) }}</span>
        </div>
        <p class="text-surface-300 text-sm mb-10">{{ t('landing.topicsMatch') }}</p>

        <!-- Ressources exemples : contenu réel -->
        <div class="space-y-2 mb-4">
          <div
            v-for="(title, i) in exTitles"
            :key="i"
            class="bg-surface-700 rounded-xl border border-surface-600 px-4 py-3.5"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <p class="text-white text-sm font-semibold leading-snug mb-1">{{ title }}</p>
                <p class="text-surface-300 text-xs leading-relaxed">{{ exDescs[i] }}</p>
              </div>
              <span class="text-xs text-brand-400 border border-brand-400/30 bg-brand-400/10 rounded-full px-2 py-0.5 shrink-0 whitespace-nowrap">
                {{ exCats[i] }}
              </span>
            </div>
          </div>
        </div>

        <!-- Lien questionnaire → ressources -->
        <p class="text-surface-400 text-sm leading-relaxed mb-12 pl-1">
          {{ t('landing.exHint') }}
        </p>

        <!-- Séparateur visuel -->
        <div class="flex items-center gap-3 mb-10">
          <div class="flex-1 border-t border-surface-600" />
          <ChevronDownIcon class="w-4 h-4 text-surface-500 shrink-0" />
          <div class="flex-1 border-t border-surface-600" />
        </div>

        <!-- Deux gros cercles -->
        <div class="flex items-center justify-center gap-8 sm:gap-14 flex-wrap">

          <div class="flex flex-col items-center gap-3">
            <button
              class="w-36 h-36 sm:w-44 sm:h-44 rounded-full bg-brand-500 hover:bg-brand-600 active:bg-brand-700 flex flex-col items-center justify-center gap-2.5 transition-all duration-150 cursor-pointer border-none shadow-lg hover:scale-105"
              @click="router.push('/profile')"
            >
              <SparklesIcon class="w-7 h-7 sm:w-8 sm:h-8 text-white" />
              <span class="text-white font-semibold text-xs sm:text-sm text-center leading-snug px-5">
                {{ hasProfile ? t('landing.q.ctaUpdate') : t('landing.q.cta') }}
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

      </div>
    </section>

  </div>
</template>
