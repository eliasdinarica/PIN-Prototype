<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import ResourceCard from '@/components/ResourceCard.vue'
import PathwayCard from '@/components/PathwayCard.vue'

const { t } = useI18n()

const props = defineProps({
  sections: { type: Array, required: true },
  showCategory: { type: Boolean, default: false },
  feedbackMap: { type: Object, default: () => ({}) },
  initialResourceId: { type: Number, default: null },
})
defineEmits(['feedback-change'])

const expandedId = ref(props.initialResourceId)

async function scrollToEl(selector) {
  if (!selector) return
  await nextTick()
  const el = document.querySelector(selector)
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 70
  window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
}

function toggle(id) {
  const opening = expandedId.value !== id
  expandedId.value = opening ? id : null
  if (opening) scrollToEl(`[data-resource-id="${id}"]`)
}

// Pathways share the expand state but use a namespaced key to avoid id clashes.
function togglePathway(id) {
  const key = `p${id}`
  const opening = expandedId.value !== key
  expandedId.value = opening ? key : null
  if (opening) scrollToEl(`[data-pathway-id="${id}"]`)
}

onMounted(() => {
  if (props.initialResourceId) scrollToEl(`[data-resource-id="${props.initialResourceId}"]`)
})

watch(() => props.initialResourceId, (newId) => {
  expandedId.value = newId
  if (newId) scrollToEl(`[data-resource-id="${newId}"]`)
})
</script>

<template>
  <template v-for="(section, si) in sections" :key="section.key + si">
    <div v-if="si > 0" class="my-5 border-t border-surface-200" />
    <p
      v-if="section.key === 'recommended' || si > 0 || section.label"
      class="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 mb-3"
      :class="section.key === 'recommended' ? 'text-brand-400' : 'text-surface-400'"
    >
      <SparklesIcon v-if="section.key === 'recommended'" class="w-3.5 h-3.5" />
      {{ section.label ?? t(`detail.${section.key}`) }}
    </p>
    <div :data-tut="si === 0 ? 'res' : undefined">
      <template v-for="item in section.items" :key="(item._kind === 'pathway' ? 'p' : 'r') + item.id">
        <PathwayCard
          v-if="item._kind === 'pathway'"
          :pathway="item"
          :category="showCategory ? item.category : null"
          :expanded="expandedId === 'p' + item.id"
          @toggle="togglePathway"
        />
        <ResourceCard
          v-else
          :resource="item"
          :category="showCategory ? item.category : null"
          :feedback="feedbackMap[item.id] ?? null"
          :expanded="expandedId === item.id"
          @toggle="toggle"
          @feedback-change="$emit('feedback-change', $event)"
        />
      </template>
    </div>
  </template>
</template>
