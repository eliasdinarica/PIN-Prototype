<script setup>
defineProps({
  label: { type: String, required: true },
  icon: { type: Object, required: true },
  active: { type: Boolean, default: false },
  recommended: { type: Boolean, default: false },
})
defineEmits(['click'])
</script>

<template>
  <button
    class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-150 cursor-pointer border-2 whitespace-nowrap shrink-0"
    :class="active
      ? 'bg-surface-500 text-white border-white/30'
      : recommended
        ? 'bg-surface-700 border-brand-600/40 text-brand-300 hover:text-white hover:border-brand-600/70'
        : 'bg-surface-700 border-surface-600 text-surface-300 hover:text-white hover:border-surface-400'"
    @click="$emit('click')"
  >
    <component :is="icon" class="w-4 h-4 shrink-0" />
    <span>{{ label }}</span>
  </button>
</template>
