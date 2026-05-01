<script setup>
defineProps({
  category: { type: Object, required: true },
})
defineEmits(['click'])
</script>

<template>
  <button
    class="group bg-white rounded-2xl p-5 text-left flex flex-col justify-between shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer border-2 border-transparent hover:border-indigo-100 active:scale-95 min-h-44 w-full"
    @click="$emit('click')"
  >
    <div>
      <div class="flex items-start justify-between gap-2 mb-3">
        <h2 class="font-bold text-indigo-950 text-base leading-snug">{{ category.name }}</h2>
        <span class="text-3xl leading-none shrink-0">{{ category.emoji }}</span>
      </div>
      <p class="text-sm text-gray-500 leading-relaxed">{{ category.description }}</p>
    </div>
    <div class="text-xs font-semibold text-gray-400 group-hover:text-indigo-500 transition-colors mt-4">Explore →</div>
  </button>
</template>
