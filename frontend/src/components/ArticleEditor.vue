<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import EditorJS from '@editorjs/editorjs'
import Header from '@editorjs/header'
import List from '@editorjs/list'
import ImageTool from '@editorjs/image'
import Quote from '@editorjs/quote'
import Marker from '@editorjs/marker'
import Delimiter from '@editorjs/delimiter'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ blocks: [] }) },
})
const emit = defineEmits(['update:modelValue'])

const holder = ref(null)
let editor = null
let suppressUpdate = false

function buildConfig(data) {
  return {
    holder: holder.value,
    placeholder: 'Start writing the article…',
    data,
    tools: {
      header: {
        class: Header,
        config: { levels: [2, 3], defaultLevel: 2, placeholder: 'Heading' },
      },
      list: { class: List, inlineToolbar: true, config: { defaultStyle: 'unordered' } },
      image: {
        class: ImageTool,
        config: {
          endpoints: { byFile: `${API}/api/editor/image/` },
          field: 'image',
          captionPlaceholder: 'Caption (optional)',
        },
      },
      quote: { class: Quote, inlineToolbar: true },
      marker: { class: Marker },
      delimiter: Delimiter,
    },
    async onChange(api) {
      if (suppressUpdate) return
      const out = await api.saver.save()
      emit('update:modelValue', out)
    },
  }
}

async function init() {
  editor = new EditorJS(buildConfig(props.modelValue || { blocks: [] }))
}

onMounted(init)

onBeforeUnmount(() => {
  if (editor && typeof editor.destroy === 'function') {
    editor.destroy()
    editor = null
  }
})

// If the parent swaps in new data (e.g. after async load), re-render the editor.
watch(() => props.modelValue, async (val) => {
  if (!editor || !val) return
  const current = await editor.save().catch(() => null)
  if (current && JSON.stringify(current.blocks) === JSON.stringify(val.blocks)) return
  suppressUpdate = true
  try {
    await editor.isReady
    await editor.render(val)
  } finally {
    suppressUpdate = false
  }
})
</script>

<template>
  <div class="article-editor">
    <div ref="holder" class="editor-holder" />
  </div>
</template>

<style scoped>
.article-editor {
  border: 1px solid var(--color-surface-300, #d4d4d8);
  border-radius: 0.75rem;
  background: white;
  padding: 0.5rem 0.5rem;
  min-height: 240px;
}
.editor-holder {
  padding: 0.5rem 2.5rem;
}
</style>

<style>
/* Editor.js needs its toolbar to be unscoped. Constrain block width so it stays readable. */
.article-editor .codex-editor__redactor {
  padding-bottom: 80px !important;
}
.article-editor .ce-block__content,
.article-editor .ce-toolbar__content {
  max-width: 100%;
}
</style>
