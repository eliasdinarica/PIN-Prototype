<script setup>
defineProps({
  label: { type: String, required: true },
  icon: { type: Object, required: true },
  active: { type: Boolean, default: false },
})
defineEmits(['click'])
</script>

<template>
  <button
    class="relative overflow-hidden px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer border-2 text-left w-full"
    :class="active
      ? 'bg-surface-500 text-white border-white/30'
      : 'bg-surface-400 text-surface-300 border-transparent hover:text-white'"
    @click="$emit('click')"
  >
    <component :is="icon" class="absolute -right-3 -bottom-3 w-16 h-16 opacity-20 pointer-events-none" />
    <span class="relative">{{ label }}</span>
  </button>
</template>
