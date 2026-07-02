<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { BookOpenIcon, DocumentTextIcon, ChatBubbleLeftRightIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200 flex flex-col">
    <header class="px-5 pt-12 pb-8 max-w-xl mx-auto w-full">
      <p class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-500 mb-4">PIN</p>
      <h1 class="text-2xl sm:text-3xl font-bold text-surface-800 leading-snug">{{ t('hub.title') }}</h1>
    </header>

    <main class="flex-1 px-5 pb-16 max-w-xl mx-auto w-full">
      <div class="flex flex-col gap-3">

        <!-- Resources (active) -->
        <button
          class="group w-full text-left bg-white border border-surface-200 shadow-sm rounded-2xl p-5 hover:border-brand-500/40 hover:shadow-md transition-all cursor-pointer"
          @click="router.push('/categories')"
        >
          <div class="flex items-center gap-4">
            <div class="w-11 h-11 rounded-xl bg-brand-500/10 flex items-center justify-center shrink-0">
              <BookOpenIcon class="w-6 h-6 text-brand-500" />
            </div>
            <div class="flex-1 min-w-0">
              <h2 class="text-surface-800 font-semibold text-base">{{ t('nav.sections.resources') }}</h2>
              <p class="text-surface-500 text-sm mt-0.5 leading-snug">{{ t('hub.resourcesDesc') }}</p>
            </div>
            <ArrowRightIcon class="w-5 h-5 text-surface-400 group-hover:text-brand-500 group-hover:translate-x-0.5 transition-all shrink-0" />
          </div>
        </button>


        <!-- CV generator (coming soon) -->
        <div class="w-full bg-surface-200/70 border border-surface-300/50 rounded-2xl p-5 opacity-60 select-none">
          <div class="flex items-center gap-4">
            <div class="w-11 h-11 rounded-xl bg-surface-300 flex items-center justify-center shrink-0">
              <DocumentTextIcon class="w-6 h-6 text-surface-500" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h2 class="text-surface-600 font-semibold text-base">{{ t('nav.sections.cv') }}</h2>
                <span class="text-xs bg-surface-300 text-surface-500 px-2 py-0.5 rounded-full">{{ t('nav.sections.comingSoon') }}</span>
              </div>
              <p class="text-surface-500 text-sm mt-0.5 leading-snug">{{ t('hub.cvDesc') }}</p>
            </div>
          </div>
        </div>

        <!-- Forum (coming soon) -->
        <div class="w-full bg-surface-200/70 border border-surface-300/50 rounded-2xl p-5 opacity-60 select-none">
          <div class="flex items-center gap-4">
            <div class="w-11 h-11 rounded-xl bg-surface-300 flex items-center justify-center shrink-0">
              <ChatBubbleLeftRightIcon class="w-6 h-6 text-surface-500" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h2 class="text-surface-600 font-semibold text-base">{{ t('nav.sections.forum') }}</h2>
                <span class="text-xs bg-surface-300 text-surface-500 px-2 py-0.5 rounded-full">{{ t('nav.sections.comingSoon') }}</span>
              </div>
              <p class="text-surface-500 text-sm mt-0.5 leading-snug">{{ t('hub.forumDesc') }}</p>
            </div>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>
