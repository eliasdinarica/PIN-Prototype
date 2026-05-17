<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { DocumentTextIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  resource: { type: Object, required: true },
  category: { type: Object, default: null },
  feedback: { type: Object, default: null }, // { id, is_useful } | null
})

const emit = defineEmits(['open', 'feedback-change'])

const tagsRef = ref(null)
const visibleCount = ref(Infinity)

onMounted(async () => {
  await nextTick()
  const container = tagsRef.value
  if (!container) return
  const containerRight = container.getBoundingClientRect().right
  const items = container.querySelectorAll('span')
  let count = 0
  for (const el of items) {
    if (el.getBoundingClientRect().right > containerRight) break
    count++
  }
  visibleCount.value = count
})

function onFeedback(isUseful) {
  if (props.feedback?.is_useful === isUseful) {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback.id, isUseful: null })
  } else {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback?.id ?? null, isUseful })
  }
}
</script>

<template>
  <div class="relative">
    <button
      class="group rounded-2xl p-4 pb-9 flex flex-col gap-2.5 shadow-sm transition-all duration-200 border-2 text-left w-full cursor-pointer bg-surface-500 border-transparent hover:shadow-md hover:border-surface-600 h-full relative overflow-hidden"
      @click="$emit('open', resource)"
    >
      <!-- Background watermark icon -->
      <DocumentTextIcon class="absolute -right-3 -top-1 w-24 h-24 text-surface-400/25 pointer-events-none" />

      <!-- Category label -->
      <p v-if="category" class="text-xs font-medium text-brand-300 relative">{{ category.name }}</p>

      <!-- Title -->
      <h3 class="font-semibold text-sm leading-snug text-white line-clamp-2 relative">{{ resource.name }}</h3>

      <!-- Description -->
      <p class="text-xs text-surface-200 line-clamp-2 leading-relaxed relative">{{ resource.description }}</p>

      <!-- Tags -->
      <div v-if="resource.tags && resource.tags.length" ref="tagsRef" class="flex gap-1 overflow-hidden relative">
        <span
          v-for="(tag, i) in resource.tags"
          v-show="i < visibleCount"
          :key="tag.id"
          class="inline-block px-1.5 py-0.5 rounded-full text-xs font-medium bg-surface-400 text-surface-200 shrink-0"
        >{{ tag.label }}</span>
      </div>
    </button>

    <!-- Feedback buttons -->
    <div class="absolute bottom-2.5 right-3 flex gap-1 z-10">
      <button
        class="w-6 h-6 flex items-center justify-center rounded transition-colors cursor-pointer bg-transparent border-none"
        :class="feedback?.is_useful === true ? 'text-green-400' : 'text-surface-300 hover:text-white'"
        @click="onFeedback(true)"
      >
        <ArrowUpIcon class="w-5 h-5" />
      </button>
      <button
        class="w-6 h-6 flex items-center justify-center rounded transition-colors cursor-pointer bg-transparent border-none"
        :class="feedback?.is_useful === false ? 'text-red-400' : 'text-surface-300 hover:text-white'"
        @click="onFeedback(false)"
      >
        <ArrowDownIcon class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>
