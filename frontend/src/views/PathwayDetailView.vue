<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as HeroIcons from '@heroicons/vue/24/outline'
import { ArrowLeftIcon } from '@heroicons/vue/24/outline'
import ArticleRenderer from '@/components/ArticleRenderer.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const pathway = ref(null)
const loading = ref(true)

function getIcon(name) {
  return HeroIcons[name] || HeroIcons.MapIcon
}

onMounted(async () => {
  const res = await fetch(`${API}/api/pathways/${route.params.id}/`)
  pathway.value = await res.json()
  loading.value = false
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <div v-if="loading" class="flex justify-center py-32">
      <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-500 rounded-full animate-spin" />
    </div>

    <template v-else-if="pathway">

      <!-- Header -->
      <header class="px-5 pt-10 pb-8 max-w-2xl mx-auto">
        <button
          class="flex items-center gap-1 text-xs text-surface-500 hover:text-surface-700 mb-5 cursor-pointer bg-transparent border-none p-0 transition-colors"
          @click="router.push('/pathways')"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5" />{{ t('pathways.back') }}
        </button>

        <div class="flex items-center gap-4 mb-3">
          <div class="w-12 h-12 rounded-2xl bg-brand-500/10 flex items-center justify-center shrink-0">
            <component :is="getIcon(pathway.icon)" class="w-7 h-7 text-brand-500" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-500 mb-1">{{ t('pathways.eyebrow') }}</p>
            <h1 class="text-xl sm:text-2xl font-bold text-surface-800 leading-snug">{{ pathway.title }}</h1>
          </div>
        </div>

        <p class="text-surface-600 text-sm leading-relaxed mb-4">{{ pathway.description }}</p>

        <!-- Step count pill -->
        <span class="inline-flex items-center gap-1.5 text-xs font-medium bg-white border border-surface-200 text-surface-600 px-3 py-1.5 rounded-full shadow-sm">
          <component :is="getIcon(pathway.icon)" class="w-3.5 h-3.5 text-brand-500" />
          {{ t('pathways.steps', { n: pathway.step_count }) }}
        </span>
      </header>

      <!-- Steps timeline -->
      <main class="px-5 pb-20 max-w-2xl mx-auto">
        <div
          v-for="(step, idx) in pathway.steps"
          :key="step.id"
          class="flex gap-4"
        >
          <!-- Left: number circle + connector -->
          <div class="flex flex-col items-center">
            <div class="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
              {{ idx + 1 }}
            </div>
            <div
              v-if="idx < pathway.steps.length - 1"
              class="w-px flex-1 bg-surface-300 mt-2 mb-0"
            />
          </div>

          <!-- Right: step card -->
          <div class="flex-1 min-w-0 pb-8">
            <div class="bg-white rounded-2xl p-5 shadow-sm border border-surface-200/60">
              <h2 class="font-bold text-surface-800 text-lg leading-snug mb-1">
                {{ step.step_label || step.resource.name }}
              </h2>
              <p v-if="step.resource.description" class="text-surface-500 text-sm leading-relaxed mb-4">
                {{ step.resource.description }}
              </p>
              <ArticleRenderer
                v-if="step.resource.body?.sections?.length || step.resource.body?.blocks?.length"
                :body="step.resource.body"
              />
            </div>
          </div>
        </div>

        <!-- Finish indicator -->
        <div class="flex gap-4">
          <div class="flex flex-col items-center">
            <div class="w-8 h-8 rounded-full bg-brand-100 border-2 border-brand-500 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
          </div>
          <div class="flex-1 pb-4 flex items-center">
            <p class="text-sm font-medium text-brand-500">{{ t('pathways.done') }}</p>
          </div>
        </div>

      </main>
    </template>

  </div>
</template>
