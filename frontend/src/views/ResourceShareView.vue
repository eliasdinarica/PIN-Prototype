<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ShareIcon, BookmarkIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/vue/24/solid'
import ArticleRenderer from '@/components/ArticleRenderer.vue'
import { useSaved } from '@/composables/useSaved'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const { isSaved, toggleSave } = useSaved()

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const resource = ref(null)
const loading = ref(true)
const notFound = ref(false)
const copied = ref(false)

const FLAGS = { en: '🇬🇧', fr: '🇫🇷', de: '🇩🇪', it: '🇮🇹', es: '🇪🇸', pt: '🇵🇹', ru: '🇷🇺' }

async function share() {
  const url = window.location.href
  try {
    if (navigator.share) await navigator.share({ title: resource.value?.name, url })
    else { await navigator.clipboard.writeText(url); copied.value = true; setTimeout(() => { copied.value = false }, 2000) }
  } catch { /* cancelled */ }
}

onMounted(async () => {
  try {
    const res = await fetch(`${API}/api/resources/${route.params.id}/`)
    if (!res.ok) { notFound.value = true; return }
    resource.value = await res.json()
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Minimal header -->
    <header class="border-b border-surface-200/70 bg-white/60 backdrop-blur">
      <div class="max-w-2xl mx-auto px-5 py-3">
        <button
          class="text-xs font-semibold tracking-[0.2em] uppercase text-brand-500 bg-transparent border-none cursor-pointer p-0"
          @click="router.push('/')"
        >
          Immiguide
        </button>
      </div>
    </header>

    <main class="max-w-2xl mx-auto px-5 py-8">

      <div v-if="loading" class="flex justify-center py-32">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-500 rounded-full animate-spin" />
      </div>

      <p v-else-if="notFound" class="text-center text-surface-500 py-32">404 — resource not found.</p>

      <template v-else-if="resource">
        <div class="space-y-3">

          <!-- Title + action bar + description -->
          <div class="bg-white rounded-2xl px-6 py-5 shadow-sm">
            <h1 class="font-bold text-2xl leading-snug text-surface-800">{{ resource.name }}</h1>
            <p v-if="resource.author" class="text-xs text-surface-400 mt-1">{{ t('resource.writtenBy', { name: resource.author }) }}</p>

            <div class="flex items-center justify-between gap-3 border-y border-surface-100 py-2.5 my-4">
              <div class="flex items-center gap-1">
                <button
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none"
                  :class="isSaved(resource.id) ? 'text-brand-600' : 'text-surface-500 hover:text-brand-600'"
                  @click="toggleSave(resource.id)"
                >
                  <component :is="isSaved(resource.id) ? BookmarkSolidIcon : BookmarkIcon" class="w-5 h-5" />
                  {{ isSaved(resource.id) ? t('actions.saved') : t('actions.save') }}
                </button>
                <button
                  class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer bg-transparent border-none text-surface-500 hover:text-brand-600"
                  @click="share"
                >
                  <ShareIcon class="w-5 h-5" />
                  {{ copied ? t('actions.copied') : t('actions.share') }}
                </button>
              </div>
              <button class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium text-surface-600 bg-transparent border-none cursor-default">
                <span>{{ FLAGS[locale] }}</span>
                <span>{{ locale.toUpperCase() }}</span>
                <ChevronDownIcon class="w-3.5 h-3.5 text-surface-400" />
              </button>
            </div>

            <p v-if="resource.description" class="text-surface-700 text-[15px] leading-relaxed">
              {{ resource.description }}
            </p>
          </div>

          <!-- Section cards -->
          <ArticleRenderer
            v-if="resource.sections?.length"
            :sections="resource.sections"
          />
        </div>
      </template>

    </main>
  </div>
</template>
