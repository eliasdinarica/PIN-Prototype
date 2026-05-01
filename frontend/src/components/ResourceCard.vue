<script setup>
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
    <div class="w-12 h-12 bg-indigo-50 group-hover:bg-indigo-100 rounded-xl flex items-center justify-center text-2xl shrink-0 transition-colors duration-200">
      📄
    </div>
    <div class="flex-1 min-w-0">
      <h3 class="font-semibold text-indigo-950 text-sm leading-snug">{{ resource.name }}</h3>
      <p class="text-xs text-gray-400 mt-1 line-clamp-2 leading-relaxed">{{ resource.description }}</p>
    </div>
    <div class="shrink-0 w-8 h-8 bg-indigo-600 group-hover:bg-indigo-700 rounded-full flex items-center justify-center text-white text-sm transition-colors duration-150">
      ↗
    </div>
  </button>
</template>
