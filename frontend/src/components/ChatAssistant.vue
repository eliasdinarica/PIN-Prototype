<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatBubbleLeftRightIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const open = ref(false)
const input = ref('')

function search() {
  const q = input.value.trim()
  if (!q) return
  router.push(`/categories/ai?q=${encodeURIComponent(q)}`)
  open.value = false
  input.value = ''
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    search()
  }
}
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

    <!-- Input panel -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-3 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-3 scale-95"
    >
      <div v-if="open" class="w-72 sm:w-80 max-w-[calc(100vw-1.5rem)] bg-white rounded-2xl shadow-2xl border border-surface-200 overflow-hidden">

        <!-- Header -->
        <div class="bg-brand-500 px-4 py-3 flex items-center gap-2">
          <ChatBubbleLeftRightIcon class="w-4 h-4 text-white shrink-0" />
          <p class="flex-1 text-white font-semibold text-sm">Find resources with AI</p>
          <button
            class="text-brand-200 hover:text-white transition-colors cursor-pointer bg-transparent border-none p-0.5 rounded"
            @click="open = false"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Search area -->
        <div class="p-3">
          <div class="flex items-end gap-2">
            <textarea
              v-model="input"
              rows="2"
              placeholder="What do you need help with?"
              class="flex-1 resize-none text-sm border border-surface-200 rounded-xl px-3 py-2 outline-none focus:border-brand-400 transition-colors bg-surface-50 text-surface-800 placeholder-surface-400 leading-relaxed"
              style="max-height: 120px; overflow-y: auto;"
              @keydown="onKeydown"
            />
            <button
              :disabled="!input.trim()"
              class="w-9 h-9 bg-brand-500 hover:bg-brand-600 disabled:bg-surface-200 rounded-xl flex items-center justify-center transition-colors cursor-pointer border-none shrink-0"
              @click="search"
            >
              <MagnifyingGlassIcon class="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

      </div>
    </Transition>

    <!-- Toggle button -->
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
