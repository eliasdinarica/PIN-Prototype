<script setup>
import { computed } from 'vue'
import * as HeroIcons from '@heroicons/vue/24/outline'

const props = defineProps({
  category: { type: Object, required: true },
})
defineEmits(['click'])

const icon = computed(() => HeroIcons[props.category.icon] || HeroIcons.StarIcon)
</script>

<template>
  <button
    class="group bg-white rounded-2xl p-5 text-left flex flex-col justify-between shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer border-2 border-transparent hover:border-slate-200 active:scale-95 min-h-44 w-full"
    @click="$emit('click')"
  >
    <div>
      <div class="flex items-start justify-between gap-2 mb-3">
        <h2 class="font-bold text-slate-800 text-base leading-snug">{{ category.name }}</h2>
        <div class="w-9 h-9 bg-surface-50 group-hover:bg-surface-100 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-200">
          <component :is="icon" class="w-5 h-5 text-surface-600" />
        </div>
      </div>
      <p class="text-sm text-gray-500 leading-relaxed">{{ category.description }}</p>
    </div>
    <div class="text-xs font-semibold text-gray-400 group-hover:text-slate-600 transition-colors mt-4">Explore →</div>
  </button>
</template>
