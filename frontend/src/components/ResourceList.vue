<script setup>
import { useI18n } from 'vue-i18n'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import ResourceCard from '@/components/ResourceCard.vue'

const { t } = useI18n()

defineProps({
  sections: { type: Array, required: true },
  showCategory: { type: Boolean, default: false },
})
defineEmits(['open'])
</script>

<template>
  <template v-for="(section, si) in sections" :key="section.key + si">
    <div v-if="si > 0" class="my-5 border-t border-surface-200" />
    <p
      v-if="section.key === 'recommended' || si > 0"
      class="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5"
      :class="section.key === 'recommended' ? 'text-brand-400' : 'text-surface-400'"
    >
      <SparklesIcon v-if="section.key === 'recommended'" class="w-3.5 h-3.5" />
      {{ t(`detail.${section.key}`) }}
    </p>
    <div class="grid grid-cols-2 gap-3">
      <ResourceCard
        v-for="resource in section.items"
        :key="resource.id"
        :resource="resource"
        :category="showCategory ? resource.category : null"
        @open="$emit('open', resource)"
      />
    </div>
  </template>
</template>
