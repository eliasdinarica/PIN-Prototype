<script setup>
import { useI18n } from 'vue-i18n'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import ResourceCard from '@/components/ResourceCard.vue'

const { t } = useI18n()

defineProps({
  sections: { type: Array, required: true },
  showCategory: { type: Boolean, default: false },
  feedbackMap: { type: Object, default: () => ({}) },
})
defineEmits(['open', 'feedback-change'])
</script>

<template>
  <template v-for="(section, si) in sections" :key="section.key + si">
    <div v-if="si > 0" class="my-5 border-t border-surface-200" />
    <p
      v-if="section.key === 'recommended' || si > 0"
      class="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 mb-3"
      :class="section.key === 'recommended' ? 'text-brand-400' : 'text-surface-400'"
    >
      <SparklesIcon v-if="section.key === 'recommended'" class="w-3.5 h-3.5" />
      {{ t(`detail.${section.key}`) }}
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3" :data-tut="si === 0 ? 'res' : undefined">
      <ResourceCard
        v-for="resource in section.items"
        :key="resource.id"
        :resource="resource"
        :category="showCategory ? resource.category : null"
        :feedback="feedbackMap[resource.id] ?? null"
        @open="$emit('open', resource)"
        @feedback-change="$emit('feedback-change', $event)"
      />
    </div>
  </template>
</template>
