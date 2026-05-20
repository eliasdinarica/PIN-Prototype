<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  TrashIcon, ArrowLeftIcon, PaperClipIcon, DocumentIcon, ChevronDownIcon,
} from '@heroicons/vue/24/outline'
import ArticleSectionsEditor from '@/components/ArticleSectionsEditor.vue'

const uid = () => (crypto?.randomUUID?.() || Math.random().toString(36).slice(2))

const NEW_RESOURCE_TEMPLATE = () => ({
  sections: [
    { id: uid(), title: 'Contenu', body: { blocks: [
      { type: 'paragraph', data: { text: '' } },
    ] } },
    { id: uid(), title: 'Personne de contact', width: 'half', body: { blocks: [
      { type: 'list', data: { style: 'unordered', items: [
        '<b>Nom :</b> ',
        '<b>Téléphone :</b> ',
        '<b>Email :</b> ',
        '<b>Adresse :</b> ',
      ] } },
    ] } },
  ],
})

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)

const name = ref('')
const description = ref('')
const categoryId = ref('')
const selectedTagIds = ref([])
const body = ref({ sections: [] })
const existingAttachments = ref([])
const newAttachments = ref([])

const categories = ref([])
const tags = ref([])
const saving = ref(false)
const loading = ref(true)
const tagSearch = ref('')

const filteredTags = computed(() => {
  const q = tagSearch.value.trim().toLowerCase()
  if (!q) return tags.value
  return tags.value.filter(t => t.label.toLowerCase().includes(q))
})

function toggleTag(tagId) {
  const i = selectedTagIds.value.indexOf(tagId)
  if (i >= 0) selectedTagIds.value.splice(i, 1)
  else selectedTagIds.value.push(tagId)
}

function onFilesPicked(e) {
  const files = Array.from(e.target.files || [])
  for (const f of files) {
    newAttachments.value.push({ file: f, label: '' })
  }
  e.target.value = ''
}

function removeNewAttachment(i) {
  newAttachments.value.splice(i, 1)
}

function removeExistingAttachment(i) {
  existingAttachments.value.splice(i, 1)
}

async function loadFormData() {
  loading.value = true
  try {
    const [catRes, tagRes] = await Promise.all([
      fetch(`${API}/api/categories-brief/`),
      fetch(`${API}/api/tags/`),
    ])
    categories.value = await catRes.json()
    tags.value = await tagRes.json()

    if (isEdit.value) {
      const r = await fetch(`${API}/api/resources/${route.params.id}/`).then(r => r.json())
      name.value = r.name
      description.value = r.description
      categoryId.value = r.category
      selectedTagIds.value = (r.tags || []).map(t => t.id)
      body.value = r.body && Array.isArray(r.body.sections) ? r.body : { sections: [] }
      existingAttachments.value = (r.attachments || []).map(a => ({
        id: a.id, file: a.file, label: a.label, order: a.order,
      }))
    } else {
      body.value = NEW_RESOURCE_TEMPLATE()
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!name.value.trim() || !categoryId.value) {
    alert('Name and category are required.')
    return
  }
  const firstSection = body.value?.sections?.[0]
  if (firstSection && !firstSection.title?.trim()) {
    alert('The first section must have a title.')
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('name', name.value)
    fd.append('description', description.value)
    fd.append('category', categoryId.value)
    for (const tid of selectedTagIds.value) fd.append('tag_ids', tid)
    fd.append('body', JSON.stringify(body.value || { sections: [] }))

    if (isEdit.value) {
      fd.append('kept_attachments', JSON.stringify(
        existingAttachments.value.map((a, i) => ({ id: a.id, label: a.label, order: i }))
      ))
      fd.append('new_attachments_meta', JSON.stringify(
        newAttachments.value.map((a, i) => ({ label: a.label, order: existingAttachments.value.length + i }))
      ))
      for (const a of newAttachments.value) fd.append('new_attachment_files', a.file)

      const res = await fetch(`${API}/api/resources/${route.params.id}/`, { method: 'PATCH', body: fd })
      if (!res.ok) throw new Error('Save failed')
    } else {
      fd.append('attachments_meta', JSON.stringify(
        newAttachments.value.map((a, i) => ({ label: a.label, order: i }))
      ))
      for (const a of newAttachments.value) fd.append('attachment_files', a.file)

      const res = await fetch(`${API}/api/resources/`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error('Save failed')
    }
    router.push('/admin/resources')
  } catch (e) {
    console.error(e)
    alert('Save failed: ' + e.message)
  } finally {
    saving.value = false
  }
}

async function deleteResource() {
  saving.value = true
  try {
    const res = await fetch(`${API}/api/resources/${route.params.id}/`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Delete failed')
    router.push('/admin/resources')
  } catch (e) {
    console.error(e)
    alert('Delete failed: ' + e.message)
  } finally {
    saving.value = false
  }
}

const collapsed = ref({ meta: false, article: false, attachments: false })
function toggle(key) { collapsed.value[key] = !collapsed.value[key] }

onMounted(loadFormData)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <!-- Sticky top action bar -->
    <div class="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-surface-200 shadow-sm">
      <div class="max-w-3xl mx-auto px-5 py-3 flex items-center gap-3">
        <button
          class="w-8 h-8 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-700 flex items-center justify-center cursor-pointer border-none shrink-0"
          @click="router.push('/admin/resources')"
        >
          <ArrowLeftIcon class="w-4 h-4" />
        </button>
        <span class="flex-1 min-w-0 font-semibold text-surface-800 text-sm truncate">
          {{ isEdit ? 'Edit resource' : 'New resource' }}
        </span>
        <button
          v-if="isEdit"
          type="button"
          :disabled="saving"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 font-medium text-sm cursor-pointer border border-red-200 disabled:opacity-50"
          @click="deleteResource"
        >
          <TrashIcon class="w-3.5 h-3.5" />
          Delete
        </button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-700 font-medium text-sm cursor-pointer border-none"
          @click="router.push('/admin/resources')"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="saving"
          class="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm cursor-pointer border-none disabled:opacity-50"
          @click="save"
        >
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-5 py-8 pb-24">

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
      </div>

      <template v-else>

        <!-- Meta -->
        <div class="bg-white rounded-2xl shadow-sm mb-4 overflow-hidden">
          <button
            type="button"
            class="w-full flex items-center justify-between px-5 py-4 cursor-pointer border-none bg-transparent hover:bg-surface-50 transition-colors"
            @click="toggle('meta')"
          >
            <span class="font-semibold text-surface-800">Info</span>
            <ChevronDownIcon
              class="w-4 h-4 text-surface-400 transition-transform duration-150"
              :class="collapsed.meta ? '-rotate-90' : ''"
            />
          </button>
          <div v-if="!collapsed.meta" class="px-5 pb-5 space-y-4 border-t border-surface-100 pt-4">
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-1.5">Name</label>
              <input
                v-model="name"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-surface-300 text-sm focus:outline-none focus:border-brand-500"
                placeholder="Resource title"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-1.5">Short description</label>
              <textarea
                v-model="description"
                rows="2"
                class="w-full px-3 py-2 rounded-xl border border-surface-300 text-sm focus:outline-none focus:border-brand-500 resize-y"
                placeholder="One-line summary shown on the resource card"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-1.5">Category</label>
              <select
                v-model="categoryId"
                class="w-full px-3 py-2 rounded-xl border border-surface-300 text-sm focus:outline-none focus:border-brand-500 cursor-pointer bg-white"
              >
                <option value="">— Choose —</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <p class="text-xs text-surface-500 mt-1">To add a new category, use the Django admin.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-1.5">
                Tags <span class="text-surface-500 font-normal">({{ selectedTagIds.length }} selected)</span>
              </label>
              <input
                v-model="tagSearch"
                type="text"
                placeholder="Search tags…"
                class="w-full px-3 py-2 rounded-xl border border-surface-300 text-sm focus:outline-none focus:border-brand-500 mb-2"
              />
              <div class="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-2 border border-surface-200 rounded-xl bg-surface-100">
                <button
                  v-for="t in filteredTags"
                  :key="t.id"
                  type="button"
                  class="px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer border-none transition-colors"
                  :class="selectedTagIds.includes(t.id) ? 'bg-brand-500 text-white' : 'bg-white text-surface-700 hover:bg-surface-200'"
                  @click="toggleTag(t.id)"
                >{{ t.label }}</button>
              </div>
              <p class="text-xs text-surface-500 mt-1">To add a new tag, use the Django admin.</p>
            </div>
          </div>
        </div>

        <!-- Article sections -->
        <div class="bg-white rounded-2xl shadow-sm mb-4 overflow-hidden">
          <button
            type="button"
            class="w-full flex items-center justify-between px-5 py-4 cursor-pointer border-none bg-transparent hover:bg-surface-50 transition-colors"
            @click="toggle('article')"
          >
            <span class="font-semibold text-surface-800">Article</span>
            <ChevronDownIcon
              class="w-4 h-4 text-surface-400 transition-transform duration-150"
              :class="collapsed.article ? '-rotate-90' : ''"
            />
          </button>
          <div v-if="!collapsed.article" class="px-5 pb-5 border-t border-surface-100 pt-4">
            <p class="text-xs text-surface-500 mb-4">
              Each section has a title and rich content. Inside a section, click <span class="font-mono">+</span> on the left of a line to add a heading, list, image, or quote. Select text to make it bold, italic, highlighted, or to add a link.
            </p>
            <ArticleSectionsEditor v-model="body" />
          </div>
        </div>

        <!-- Attachments -->
        <div class="bg-white rounded-2xl shadow-sm mb-4 overflow-hidden">
          <button
            type="button"
            class="w-full flex items-center justify-between px-5 py-4 cursor-pointer border-none bg-transparent hover:bg-surface-50 transition-colors"
            @click="toggle('attachments')"
          >
            <span class="font-semibold text-surface-800">
              Attachments
              <span v-if="existingAttachments.length || newAttachments.length" class="text-xs font-normal text-surface-500 ml-1">
                ({{ existingAttachments.length + newAttachments.length }})
              </span>
            </span>
            <ChevronDownIcon
              class="w-4 h-4 text-surface-400 transition-transform duration-150"
              :class="collapsed.attachments ? '-rotate-90' : ''"
            />
          </button>
          <div v-if="!collapsed.attachments" class="px-5 pb-5 border-t border-surface-100 pt-4">
            <div v-if="!existingAttachments.length && !newAttachments.length" class="text-sm text-surface-500 mb-3">
              No files yet.
            </div>
            <div class="space-y-2 mb-3">
              <div
                v-for="(a, i) in existingAttachments"
                :key="`ex-${a.id}`"
                class="flex items-center gap-2 p-2 rounded-xl border border-surface-200 bg-surface-100"
              >
                <DocumentIcon class="w-5 h-5 text-surface-500 shrink-0" />
                <div class="flex-1 min-w-0">
                  <input
                    v-model="a.label"
                    type="text"
                    :placeholder="a.file.split('/').pop()"
                    class="w-full px-2 py-1 rounded border border-surface-300 text-sm bg-white focus:outline-none focus:border-brand-500"
                  />
                  <a :href="a.file" target="_blank" class="text-xs text-brand-500 hover:underline truncate block mt-1">
                    {{ a.file.split('/').pop() }}
                  </a>
                </div>
                <button
                  type="button"
                  class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 text-red-500 cursor-pointer bg-transparent border-none"
                  @click="removeExistingAttachment(i)"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
              <div
                v-for="(a, i) in newAttachments"
                :key="`new-${i}`"
                class="flex items-center gap-2 p-2 rounded-xl border-2 border-dashed border-brand-300 bg-brand-50"
              >
                <DocumentIcon class="w-5 h-5 text-brand-500 shrink-0" />
                <div class="flex-1 min-w-0">
                  <input
                    v-model="a.label"
                    type="text"
                    :placeholder="a.file.name"
                    class="w-full px-2 py-1 rounded border border-surface-300 text-sm bg-white focus:outline-none focus:border-brand-500"
                  />
                  <p class="text-xs text-surface-500 truncate mt-1">{{ a.file.name }}</p>
                </div>
                <button
                  type="button"
                  class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 text-red-500 cursor-pointer bg-transparent border-none"
                  @click="removeNewAttachment(i)"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
            <label class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-100 hover:bg-surface-200 text-surface-700 text-sm font-medium cursor-pointer border border-surface-300 w-fit">
              <PaperClipIcon class="w-4 h-4" /> Add file(s)
              <input type="file" multiple class="hidden" @change="onFilesPicked" />
            </label>
          </div>
        </div>

      </template>

    </div>
  </div>
</template>
