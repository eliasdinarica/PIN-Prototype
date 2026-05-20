<script setup>
import { ref, watch } from 'vue'
import {
  PlusIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon,
  DocumentTextIcon, UserIcon, ChatBubbleLeftRightIcon, Squares2X2Icon,
  ViewColumnsIcon, Bars3Icon, ChevronRightIcon,
} from '@heroicons/vue/24/outline'
import ArticleEditor from '@/components/ArticleEditor.vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ sections: [] }) },
})
const emit = defineEmits(['update:modelValue'])

const uid = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2))

const sections = ref([])
const showTemplates = ref(false)
const collapsedMap = ref({})

function syncFromProps() {
  const incoming = (props.modelValue?.sections || []).map(s => ({
    id: s.id || uid(),
    title: s.title || '',
    width: s.width === 'half' ? 'half' : 'full',
    body: s.body && Array.isArray(s.body.blocks) ? s.body : { blocks: [] },
  }))
  sections.value = incoming
}
syncFromProps()

watch(() => props.modelValue, syncFromProps, { deep: false })

function emitChange() {
  emit('update:modelValue', {
    sections: sections.value.map(s => ({ id: s.id, title: s.title, width: s.width, body: s.body })),
  })
}

function toggleCollapsed(id) {
  const next = { ...collapsedMap.value }
  if (next[id]) delete next[id]
  else next[id] = true
  collapsedMap.value = next
}

function toggleWidth(i) {
  sections.value[i].width = sections.value[i].width === 'half' ? 'full' : 'half'
  emitChange()
}

function onTitleChange(i, value) {
  sections.value[i].title = value
  emitChange()
}

function onBodyChange(i, value) {
  sections.value[i].body = value
  emitChange()
}

function move(i, delta) {
  const j = i + delta
  if (j < 0 || j >= sections.value.length) return
  const tmp = sections.value[i]
  sections.value.splice(i, 1)
  sections.value.splice(j, 0, tmp)
  emitChange()
}

function remove(i) {
  sections.value.splice(i, 1)
  emitChange()
}

const TEMPLATES = [
  {
    key: 'contenu',
    label: 'Contenu',
    icon: DocumentTextIcon,
    build: () => ({ title: 'Contenu', body: { blocks: [
      { type: 'paragraph', data: { text: '' } },
    ] } }),
  },
  {
    key: 'contact',
    label: 'Personne de contact',
    icon: UserIcon,
    build: () => ({ title: 'Personne de contact', width: 'half', body: { blocks: [
      { type: 'list', data: { style: 'unordered', items: [
        '<b>Nom :</b> ',
        '<b>Téléphone :</b> ',
        '<b>Email :</b> ',
        '<b>Adresse :</b> ',
      ] } },
    ] } }),
  },
  {
    key: 'questions',
    label: 'Questions fréquentes',
    icon: ChatBubbleLeftRightIcon,
    build: () => ({ title: 'Questions fréquentes', body: { blocks: [
      { type: 'header', data: { text: 'Question 1 ?', level: 3 } },
      { type: 'paragraph', data: { text: '' } },
    ] } }),
  },
  {
    key: 'custom',
    label: 'Section vide',
    icon: Squares2X2Icon,
    build: () => ({ title: '', body: { blocks: [] } }),
  },
]

function addFromTemplate(tpl) {
  const built = tpl.build()
  sections.value.push({
    id: uid(),
    title: built.title,
    width: built.width || 'full',
    body: built.body,
  })
  showTemplates.value = false
  emitChange()
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="!sections.length" class="text-sm text-surface-500 italic px-1">
      No sections yet. Add one below.
    </div>

    <div class="flex flex-wrap gap-3 items-start">
      <div
        v-for="(s, i) in sections"
        :key="s.id"
        class="border rounded-2xl bg-surface-100 overflow-hidden flex flex-col min-w-0"
        :class="[
          s.width === 'half' ? 'w-full md:w-[calc(50%-0.375rem)]' : 'w-full',
          i === 0 && !s.title ? 'border-red-300' : 'border-surface-200',
        ]"
      >
        <!-- Section header bar -->
        <div class="flex items-center gap-1.5 px-3 py-2 bg-surface-200/60 border-b border-surface-200">
          <!-- Collapse toggle -->
          <button
            type="button"
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-surface-300 text-surface-500 cursor-pointer bg-transparent border-none shrink-0 transition-transform duration-150"
            :class="collapsedMap[s.id] ? '' : 'rotate-90'"
            :title="collapsedMap[s.id] ? 'Expand' : 'Collapse'"
            @click="toggleCollapsed(s.id)"
          >
            <ChevronRightIcon class="w-3.5 h-3.5" />
          </button>

          <input
            type="text"
            :value="s.title"
            :placeholder="i === 0 ? 'Title (required)…' : 'Section title…'"
            class="flex-1 min-w-0 px-2 py-1 rounded border hover:border-surface-300 focus:border-brand-500 focus:bg-white focus:outline-none text-sm font-semibold bg-transparent"
            :class="i === 0 && !s.title ? 'border-red-300 bg-red-50/60' : 'border-transparent'"
            @input="e => onTitleChange(i, e.target.value)"
          />
          <span v-if="i === 0 && !s.title" class="text-red-400 text-xs shrink-0 font-medium">required</span>

          <button
            type="button"
            class="w-7 h-7 flex items-center justify-center rounded hover:bg-surface-300 cursor-pointer bg-transparent border-none shrink-0"
            :class="s.width === 'half' ? 'text-brand-600' : 'text-surface-500'"
            :title="s.width === 'half' ? 'Make full width' : 'Make half width'"
            @click="toggleWidth(i)"
          >
            <ViewColumnsIcon v-if="s.width === 'half'" class="w-4 h-4" />
            <Bars3Icon v-else class="w-4 h-4" />
          </button>
          <button
            type="button"
            class="w-7 h-7 flex items-center justify-center rounded hover:bg-surface-300 text-surface-700 cursor-pointer bg-transparent border-none disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
            :disabled="i === 0"
            title="Move up"
            @click="move(i, -1)"
          >
            <ChevronUpIcon class="w-4 h-4" />
          </button>
          <button
            type="button"
            class="w-7 h-7 flex items-center justify-center rounded hover:bg-surface-300 text-surface-700 cursor-pointer bg-transparent border-none disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
            :disabled="i === sections.length - 1"
            title="Move down"
            @click="move(i, 1)"
          >
            <ChevronDownIcon class="w-4 h-4" />
          </button>
          <button
            type="button"
            class="w-7 h-7 flex items-center justify-center rounded hover:bg-red-100 text-red-500 cursor-pointer bg-transparent border-none shrink-0"
            title="Delete section"
            @click="remove(i)"
          >
            <TrashIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Section body editor (hidden when collapsed) -->
        <div v-if="!collapsedMap[s.id]" class="p-2 bg-white flex-1 min-w-0">
          <ArticleEditor :model-value="s.body" @update:model-value="v => onBodyChange(i, v)" />
        </div>
      </div>
    </div>

    <!-- Add section -->
    <div class="relative">
      <button
        v-if="!showTemplates"
        type="button"
        class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm cursor-pointer border-none w-full justify-center"
        @click="showTemplates = true"
      >
        <PlusIcon class="w-4 h-4" />
        Add section
      </button>

      <div v-else class="border border-surface-200 rounded-2xl bg-white p-3 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-semibold text-surface-700">Choose a template</p>
          <button
            type="button"
            class="text-xs text-surface-500 hover:text-surface-700 cursor-pointer bg-transparent border-none"
            @click="showTemplates = false"
          >Cancel</button>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            v-for="tpl in TEMPLATES"
            :key="tpl.key"
            type="button"
            class="flex flex-col items-center gap-1.5 p-3 rounded-xl border border-surface-200 hover:border-brand-400 hover:bg-brand-50 cursor-pointer text-surface-700 transition-colors bg-white"
            @click="addFromTemplate(tpl)"
          >
            <component :is="tpl.icon" class="w-6 h-6 text-brand-500" />
            <span class="text-xs font-medium text-center leading-tight">{{ tpl.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
