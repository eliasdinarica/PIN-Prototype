<script setup>
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

defineProps({
  resource: { type: Object, required: true },
})
defineEmits(['open'])
</script>

<template>
  <button
    class="group bg-surface-500 rounded-2xl p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-all duration-200 border-2 border-transparent hover:border-surface-600 text-left w-full cursor-pointer"
    @click="$emit('open', resource)"
  >
    
    <div class="flex-1 min-w-0">
      <h3 class="font-semibold text-white text-base leading-snug">{{ resource.name }}</h3>
      <p class="text-sm text-surface-200 mt-1 line-clamp-2 leading-relaxed">{{ resource.description }}</p>
      <div v-if="resource.tags && resource.tags.length" class="flex flex-wrap gap-1.5 mt-2">
        <span
          v-for="tag in resource.tags"
          :key="tag.id"
          class="inline-block px-2 py-0.5 rounded-full bg-surface-400 text-surface-200 text-xs font-medium"
        >
          {{ tag.label }}
        </span>
      </div>
    </div>
    <div class="w-12 h-12 bg-surface-400 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-200">
      <DocumentTextIcon class="w-6 h-6 text-surface-800" />
    </div>
  </button>
</template>
