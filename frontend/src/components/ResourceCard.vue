<script setup>
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

defineProps({
  resource: { type: Object, required: true },
  category: { type: Object, default: null },
})
defineEmits(['open'])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <button
      class="group rounded-2xl p-4 flex flex-col gap-2.5 shadow-sm transition-all duration-200 border-2 text-left w-full cursor-pointer bg-surface-500 border-transparent hover:shadow-md hover:border-surface-600 h-full relative overflow-hidden"
      @click="$emit('open', resource)"
    >
      <!-- Background watermark icon -->
      <DocumentTextIcon class="absolute -right-4 -bottom-4 w-24 h-24 text-surface-400/25 pointer-events-none" />

      <!-- Category label -->
      <p v-if="category" class="text-xs font-medium text-brand-300 relative">{{ category.name }}</p>

      <!-- Title -->
      <h3 class="font-semibold text-sm leading-snug text-white line-clamp-2 relative">{{ resource.name }}</h3>

      <!-- Description -->
      <p class="text-xs text-surface-200 line-clamp-2 leading-relaxed relative">{{ resource.description }}</p>

      <!-- Tags -->
      <div v-if="resource.tags && resource.tags.length" class="flex flex-wrap gap-1 relative">
        <span
          v-for="tag in resource.tags"
          :key="tag.id"
          class="inline-block px-1.5 py-0.5 rounded-full text-xs font-medium bg-surface-400 text-surface-200"
        >{{ tag.label }}</span>
      </div>
    </button>
  </div>
</template>
