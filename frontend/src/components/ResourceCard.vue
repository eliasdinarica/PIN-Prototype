<script setup>
import { DocumentTextIcon, ArrowTopRightOnSquareIcon } from '@heroicons/vue/24/outline'

defineProps({
  resource: { type: Object, required: true },
})
defineEmits(['open'])
</script>

<template>
  <button
    class="group bg-white rounded-2xl p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-all duration-200 border-2 border-transparent hover:border-indigo-100 text-left w-full cursor-pointer"
    @click="$emit('open', resource)"
  >
    <div class="w-12 h-12 bg-indigo-50 group-hover:bg-indigo-100 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-200">
      <DocumentTextIcon class="w-6 h-6 text-indigo-600" />
    </div>
    <div class="flex-1 min-w-0">
      <h3 class="font-semibold text-indigo-950 text-sm leading-snug">{{ resource.name }}</h3>
      <p class="text-xs text-gray-400 mt-1 line-clamp-2 leading-relaxed">{{ resource.description }}</p>
      <div v-if="resource.tags && resource.tags.length" class="flex flex-wrap gap-1.5 mt-2">
        <span
          v-for="tag in resource.tags"
          :key="tag.id"
          class="inline-block px-2 py-0.5 rounded-full bg-violet-100 text-violet-600 text-xs font-medium"
        >
          {{ tag.label }}
        </span>
      </div>
    </div>
    <div class="shrink-0 w-8 h-8 bg-indigo-600 group-hover:bg-indigo-700 rounded-full flex items-center justify-center transition-colors duration-150">
      <ArrowTopRightOnSquareIcon class="w-4 h-4 text-white" />
    </div>
  </button>
</template>
