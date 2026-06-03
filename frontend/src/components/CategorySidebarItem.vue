<script setup>
defineProps({
  label: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  active: { type: Boolean, default: false },
})
defineEmits(['click'])
</script>

<template>
  <button
    class="flex items-center gap-3 w-full flex-1 min-h-0 px-4 text-sm rounded-md transition-all duration-150 cursor-pointer text-left border-l-2"
    :class="active
      ? 'border-brand-400 bg-surface-400 font-semibold text-white'
      : 'border-transparent text-surface-200 hover:bg-surface-400 hover:text-white'"
    @click="$emit('click')"
  >
    <component :is="icon" class="w-8 h-8 shrink-0" />
    <span>{{ label }}</span>
  </button>
</template>
