<script setup>
import { DocumentTextIcon, SparklesIcon } from '@heroicons/vue/24/outline'

defineProps({
  resource: { type: Object, required: true },
  recommended: { type: Boolean, default: false },
})
defineEmits(['open'])
</script>

<template>
  <button
    class="group rounded-2xl p-5 flex items-center gap-4 shadow-sm transition-all duration-200 border-2 text-left w-full cursor-pointer bg-surface-500 border-transparent hover:shadow-md hover:border-surface-600"
      
    @click="$emit('open', resource)"
  >
    <div class="flex-1 min-w-0">
      <h3
        class="font-semibold text-base leading-snug"
        :class="recommended ? 'text-white' : 'text-surface-300'"
      >{{ resource.name }}</h3>
      <p
        class="text-sm mt-1 line-clamp-2 leading-relaxed text-surface-200"
      >{{ resource.description }}</p>
      <div v-if="resource.tags && resource.tags.length" class="flex flex-wrap gap-1.5 mt-2">
        <span
          v-for="tag in resource.tags"
          :key="tag.id"
          class="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-surface-400 text-surface-200"
          
        >
          {{ tag.label }}
        </span>
      </div>
    </div>
    <div
      class="relative w-12 h-12 rounded-xl flex items-center justify-center shrink-0 bg-surface-400"
      
    >
      <DocumentTextIcon
        class="w-6 h-6 text-surface-800"
      />
    </div>
  </button>
</template>
