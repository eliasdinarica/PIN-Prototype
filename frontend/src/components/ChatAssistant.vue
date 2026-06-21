<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ChatBubbleLeftRightIcon, XMarkIcon, MagnifyingGlassIcon, MapIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const { t } = useI18n()
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const open = ref(false)
const input = ref('')
const loading = ref(false)
const reply = ref('')
const results = ref([])      // resources
const pathways = ref([])
const error = ref('')

async function search() {
  const q = input.value.trim()
  if (!q) return
  loading.value = true
  reply.value = ''; results.value = []; pathways.value = []; error.value = ''
  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q, history: [] }),
    })
    const data = await res.json()
    if (data.error) error.value = data.error
    else { reply.value = data.reply; results.value = data.resources || []; pathways.value = data.pathways || [] }
  } catch {
    error.value = 'Connection error. Please try again.'
  }
  loading.value = false
}

function openResource(id) {
  router.push(`/r/${id}`)
  open.value = false
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); search() }
}
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-3 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-3 scale-95"
    >
      <div v-if="open" class="w-80 max-w-[calc(100vw-1.5rem)] bg-white rounded-2xl shadow-2xl border border-surface-200 overflow-hidden flex flex-col">

        <div class="bg-brand-500 px-4 py-3 flex items-center gap-2 shrink-0">
          <ChatBubbleLeftRightIcon class="w-4 h-4 text-white shrink-0" />
          <p class="flex-1 text-white font-semibold text-sm">{{ t('assistant.title') }}</p>
          <button class="text-brand-200 hover:text-white transition-colors cursor-pointer bg-transparent border-none p-0.5 rounded" @click="open = false">
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>

        <div class="p-3">
          <div class="flex items-end gap-2">
            <textarea
              v-model="input"
              rows="2"
              :placeholder="t('assistant.placeholder')"
              class="flex-1 resize-none text-sm border border-surface-200 rounded-xl px-3 py-2 outline-none focus:border-brand-400 transition-colors bg-surface-50 text-surface-800 placeholder-surface-400 leading-relaxed"
              style="max-height: 120px; overflow-y: auto;"
              @keydown="onKeydown"
            />
            <button
              :disabled="!input.trim() || loading"
              class="w-9 h-9 bg-brand-500 hover:bg-brand-600 disabled:bg-surface-200 rounded-xl flex items-center justify-center transition-colors cursor-pointer border-none shrink-0"
              @click="search"
            >
              <MagnifyingGlassIcon class="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        <!-- Results -->
        <div v-if="loading || reply || error" class="px-3 pb-3 max-h-80 overflow-y-auto">
          <div v-if="loading" class="flex justify-center py-6">
            <div class="w-6 h-6 border-4 border-surface-200 border-t-brand-500 rounded-full animate-spin" />
          </div>
          <p v-else-if="error" class="text-red-500 text-sm">{{ error }}</p>
          <template v-else>
            <p v-if="reply" class="text-surface-600 text-sm leading-relaxed mb-3">{{ reply }}</p>
            <button
              v-for="pw in pathways"
              :key="'p' + pw.id"
              class="w-full text-left flex items-start gap-2 p-2.5 rounded-xl border border-surface-200 hover:border-brand-400 hover:bg-brand-50 transition-colors cursor-pointer mb-2 bg-transparent"
              @click="openResource(pw.steps?.[0]?.resource?.id)"
              v-show="pw.steps?.length"
            >
              <MapIcon class="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
              <span class="text-sm font-medium text-surface-800 leading-snug">{{ pw.title }}</span>
            </button>
            <button
              v-for="r in results"
              :key="r.id"
              class="w-full text-left p-2.5 rounded-xl border border-surface-200 hover:border-brand-400 hover:bg-brand-50 transition-colors cursor-pointer mb-2 bg-transparent"
              @click="openResource(r.id)"
            >
              <p v-if="r.category" class="text-xs text-brand-400 mb-0.5">{{ r.category.name }}</p>
              <p class="text-sm font-medium text-surface-800 leading-snug">{{ r.name }}</p>
            </button>
          </template>
        </div>

      </div>
    </Transition>

    <button
      class="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 active:bg-brand-700 text-white h-10 px-4 rounded-full shadow-xl transition-all duration-150 cursor-pointer border-none"
      @click="open = !open"
    >
      <Transition
        mode="out-in"
        enter-active-class="transition-all duration-150 ease-out"
        enter-from-class="opacity-0 scale-75"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-100 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-75"
      >
        <XMarkIcon v-if="open" class="w-4 h-4 text-white shrink-0" />
        <ChatBubbleLeftRightIcon v-else class="w-4 h-4 text-white shrink-0" />
      </Transition>
      <span class="text-sm font-semibold">IA</span>
    </button>

  </div>
</template>
