<script setup>
import { useI18n } from 'vue-i18n'
import { MapIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import ArticleRenderer from '@/components/ArticleRenderer.vue'

const { t } = useI18n()

defineProps({
  pathway: { type: Object, required: true },
  category: { type: Object, default: null },
  expanded: { type: Boolean, default: false },
})
defineEmits(['toggle'])
</script>

<template>
  <div :data-pathway-id="pathway.id" class="border-b border-surface-300/70">

    <!-- Collapsed row -->
    <button
      v-if="!expanded"
      class="flex items-center w-full py-4 text-left cursor-pointer bg-transparent border-none gap-4 group"
      @click="$emit('toggle', pathway.id)"
    >
      <div class="flex-1 min-w-0">
        <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
        <h3 class="font-semibold text-lg leading-snug text-surface-800 group-hover:text-brand-500 transition-colors">
          {{ pathway.title }}
        </h3>
      </div>
      <div class="flex items-center gap-3 shrink-0">
        <span class="flex items-center gap-1 text-xs text-brand-500 bg-brand-50 px-2 py-0.5 rounded-full">
          <MapIcon class="w-3 h-3 shrink-0" />{{ t('nav.sections.pathways') }}
        </span>
        <ChevronDownIcon class="w-5 h-5 text-surface-400 shrink-0" />
      </div>
    </button>

    <!-- Expanded — description + steps -->
    <div v-else class="py-4 space-y-3">

      <!-- Title + description bubble -->
      <div class="bg-white rounded-2xl px-6 py-5 shadow-sm">
        <button
          class="flex items-start w-full text-left cursor-pointer bg-transparent border-none gap-3"
          @click="$emit('toggle', pathway.id)"
        >
          <div class="flex-1 min-w-0">
            <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
            <h3 class="font-bold text-xl leading-snug text-surface-800">{{ pathway.title }}</h3>
            <span class="inline-flex items-center gap-1 text-xs text-brand-500 mt-1">
              <MapIcon class="w-3.5 h-3.5 shrink-0" />{{ t('pathways.steps', { n: pathway.step_count }) }}
            </span>
          </div>
          <ChevronDownIcon class="w-5 h-5 text-brand-500 shrink-0 rotate-180 mt-1" />
        </button>
        <p v-if="pathway.description" class="text-surface-700 text-[15px] leading-relaxed mt-3 pt-3 border-t border-surface-100">
          {{ pathway.description }}
        </p>
      </div>

      <!-- Steps timeline -->
      <div
        v-for="(step, idx) in pathway.steps"
        :key="step.id"
        class="flex gap-4"
      >
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
            {{ idx + 1 }}
          </div>
          <div v-if="idx < pathway.steps.length - 1" class="w-px flex-1 bg-surface-300 mt-2" />
        </div>
        <div class="flex-1 min-w-0 pb-2">
          <div class="bg-white rounded-2xl p-5 shadow-sm border border-surface-200/60">
            <h4 class="font-bold text-surface-800 text-lg leading-snug mb-1">
              {{ step.step_label || step.resource.name }}
            </h4>
            <p v-if="step.resource.description" class="text-surface-500 text-sm leading-relaxed mb-3">
              {{ step.resource.description }}
            </p>
            <ArticleRenderer
              v-if="step.resource.sections?.length"
              :sections="step.resource.sections"
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
