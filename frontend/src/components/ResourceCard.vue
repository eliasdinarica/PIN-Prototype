<script setup>
import { useI18n } from 'vue-i18n'
import { SparklesIcon, UsersIcon, ShieldCheckIcon, ArrowDownTrayIcon, DocumentTextIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/outline'
import ArticleRenderer from '@/components/ArticleRenderer.vue'

const { t } = useI18n()

const props = defineProps({
  resource: { type: Object, required: true },
  category: { type: Object, default: null },
  feedback: { type: Object, default: null },
  expanded: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'feedback-change'])

function onFeedback(isUseful) {
  if (props.feedback?.is_useful === isUseful) {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback.id, isUseful: null })
  } else {
    emit('feedback-change', { resourceId: props.resource.id, feedbackId: props.feedback?.id ?? null, isUseful })
  }
}

function filenameFromUrl(url) {
  try { return decodeURIComponent(url.split('/').pop().split('?')[0]) } catch { return url }
}
</script>

<template>
  <div class="border-b border-surface-300/70">

    <!-- Collapsed row -->
    <button
      class="flex items-center w-full py-4 text-left cursor-pointer bg-transparent border-none gap-4 group"
      @click="$emit('toggle', resource.id)"
    >
      <!-- Title (vertically centered by parent items-center) -->
      <div class="flex-1 min-w-0">
        <p v-if="category" class="text-xs font-medium text-brand-400 mb-0.5">{{ category.name }}</p>
        <h3
          class="font-semibold text-lg leading-snug transition-colors"
          :class="expanded ? 'text-brand-500' : 'text-surface-800 group-hover:text-brand-500'"
        >{{ resource.name }}</h3>
      </div>

      <!-- Right column: badges pinned top, arrows centered in remaining space -->
      <div class="flex flex-col items-end self-stretch shrink-0">
        <div class="flex flex-col items-end gap-0.5 min-h-4">
          <span v-if="resource.recommended_by_system" class="flex items-center gap-1 text-xs text-brand-500">
            <SparklesIcon class="w-3 h-3 shrink-0" />{{ t('community.bySystem') }}
          </span>
          <span v-if="resource.community_by_language" class="flex items-center gap-1 text-xs text-cyan-600">
            <UsersIcon class="w-3 h-3 shrink-0" />{{ t('community.byLanguage', { code: resource.community_by_language.toUpperCase() }) }}
          </span>
          <span v-if="resource.community_by_status" class="flex items-center gap-1 text-xs text-amber-600">
            <ShieldCheckIcon class="w-3 h-3 shrink-0" />{{ t('community.byStatus', { code: resource.community_by_status }) }}
          </span>
        </div>
        <div class="flex-1 flex items-center">
          <div class="flex items-center gap-0.5">
            <button
              class="w-7 h-7 flex items-center justify-center rounded transition-colors cursor-pointer bg-transparent border-none"
              :class="feedback?.is_useful === true ? 'text-green-500' : 'text-surface-400 hover:text-surface-700'"
              @click.stop="onFeedback(true)"
            >
              <ArrowUpIcon class="w-4 h-4" />
            </button>
            <button
              class="w-7 h-7 flex items-center justify-center rounded transition-colors cursor-pointer bg-transparent border-none"
              :class="feedback?.is_useful === false ? 'text-red-500' : 'text-surface-400 hover:text-surface-700'"
              @click.stop="onFeedback(false)"
            >
              <ArrowDownIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </button>

    <!-- Expanded content -->
    <div v-if="expanded" class="pb-6">
      <div class="bg-white rounded-xl px-6 py-5 shadow-sm">
        <p v-if="resource.description" class="text-gray-600 leading-relaxed mb-4">{{ resource.description }}</p>
        <ArticleRenderer
          v-if="resource.body?.sections?.length || resource.body?.blocks?.length"
          :body="resource.body"
        />
        <div v-if="resource.attachments?.length" class="mt-6 pt-5 border-t border-gray-100">
          <p class="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Fichiers</p>
          <div class="space-y-2">
            <a
              v-for="a in resource.attachments"
              :key="a.id"
              :href="a.file"
              target="_blank"
              download
              class="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:border-brand-400 hover:bg-brand-50 transition-colors no-underline"
            >
              <DocumentTextIcon class="w-5 h-5 text-brand-500 shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-800 text-sm truncate">{{ a.label || filenameFromUrl(a.file) }}</p>
                <p v-if="a.label" class="text-xs text-gray-400 truncate">{{ filenameFromUrl(a.file) }}</p>
              </div>
              <ArrowDownTrayIcon class="w-4 h-4 text-gray-400 shrink-0" />
            </a>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
