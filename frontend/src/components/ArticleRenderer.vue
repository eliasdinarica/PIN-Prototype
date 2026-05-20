<script setup>
import { computed } from 'vue'

const props = defineProps({
  body: { type: Object, default: () => ({ sections: [] }) },
})

// Minimal HTML sanitizer: only keep inline tags that Editor.js produces.
const ALLOWED_TAGS = new Set(['b', 'strong', 'i', 'em', 'u', 'mark', 'a', 'br', 'code'])

function sanitize(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, 'text/html')
  const walk = (node) => {
    const children = Array.from(node.childNodes)
    for (const child of children) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName.toLowerCase()
        if (!ALLOWED_TAGS.has(tag)) {
          const text = document.createTextNode(child.textContent || '')
          child.replaceWith(text)
          continue
        }
        for (const attr of Array.from(child.attributes)) {
          if (tag === 'a' && attr.name === 'href') {
            const val = attr.value.trim().toLowerCase()
            if (val.startsWith('javascript:') || val.startsWith('data:')) {
              child.removeAttribute(attr.name)
            }
            continue
          }
          child.removeAttribute(attr.name)
        }
        if (tag === 'a') {
          child.setAttribute('target', '_blank')
          child.setAttribute('rel', 'noopener noreferrer')
        }
        walk(child)
      }
    }
  }
  walk(doc.body.firstChild)
  return doc.body.firstChild.innerHTML
}

const sections = computed(() => {
  const b = props.body || {}
  if (Array.isArray(b.sections)) return b.sections
  // Back-compat: a flat { blocks } body — wrap it as a single untitled section.
  if (Array.isArray(b.blocks)) return [{ title: '', body: { blocks: b.blocks } }]
  return []
})

function blocksOf(section) {
  return Array.isArray(section?.body?.blocks) ? section.body.blocks : []
}
</script>

<template>
  <article class="article-renderer">
    <div class="ar-sections">
      <section
        v-for="(section, sIdx) in sections"
        :key="sIdx"
        class="ar-section"
        :class="section.width === 'half' ? 'ar-section-half' : 'ar-section-full'"
      >
        <h2 v-if="section.title" class="ar-section-title">{{ section.title }}</h2>

        <template v-for="(b, i) in blocksOf(section)" :key="`${sIdx}-${i}`">
          <component
            v-if="b.type === 'header'"
            :is="`h${b.data?.level || 3}`"
            class="ar-header"
            :class="`ar-header-l${b.data?.level || 3}`"
            v-html="sanitize(b.data?.text || '')"
          />
          <p
            v-else-if="b.type === 'paragraph'"
            class="ar-paragraph"
            v-html="sanitize(b.data?.text || '')"
          />
          <ul
            v-else-if="b.type === 'list' && b.data?.style !== 'ordered'"
            class="ar-list"
          >
            <li v-for="(item, j) in b.data?.items || []" :key="j" v-html="sanitize(typeof item === 'string' ? item : item?.content || '')" />
          </ul>
          <ol
            v-else-if="b.type === 'list' && b.data?.style === 'ordered'"
            class="ar-list ar-list-ordered"
          >
            <li v-for="(item, j) in b.data?.items || []" :key="j" v-html="sanitize(typeof item === 'string' ? item : item?.content || '')" />
          </ol>
          <blockquote v-else-if="b.type === 'quote'" class="ar-quote">
            <p v-html="sanitize(b.data?.text || '')" />
            <cite v-if="b.data?.caption" v-html="sanitize(b.data.caption)" />
          </blockquote>
          <figure v-else-if="b.type === 'image'" class="ar-figure">
            <img :src="b.data?.file?.url" :alt="b.data?.caption || ''" />
            <figcaption v-if="b.data?.caption" v-html="sanitize(b.data.caption)" />
          </figure>
          <hr v-else-if="b.type === 'delimiter'" class="ar-delimiter" />
        </template>
      </section>
    </div>

    <p v-if="!sections.length" class="ar-empty">No content yet.</p>
  </article>
</template>

<style scoped>
.article-renderer { color: rgb(63 63 70); overflow-x: hidden; max-width: 100%; }
.ar-sections {
  display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: flex-start;
}
.ar-section { min-width: 0; overflow-x: hidden; }
.ar-section-full { width: 100%; }
.ar-section-half { width: 100%; }
@media (min-width: 768px) {
  .ar-section-half { width: calc(50% - 0.75rem); }
}
.ar-section-title {
  font-size: 1.35rem; font-weight: 700; color: rgb(24 24 27);
  margin: 0 0 0.875rem; padding-bottom: 0.5rem;
  border-bottom: 2px solid rgb(228 228 231);
}
.ar-header { font-weight: 600; color: rgb(39 39 42); margin: 1.5rem 0 0.75rem; }
.ar-header-l2 { font-size: 1.35rem; }
.ar-header-l3 { font-size: 1.15rem; }
.ar-paragraph { font-size: 1rem; line-height: 1.65; margin: 0 0 1rem; white-space: pre-wrap; }
.ar-list { margin: 0 0 1rem; padding-left: 1.25rem; line-height: 1.65; list-style: disc; }
.ar-list li { margin-bottom: 0.25rem; }
.ar-list-ordered { list-style: decimal; }
.ar-quote { margin: 1rem 0; padding: 0.5rem 1rem; border-left: 3px solid rgb(212 212 216); color: rgb(82 82 91); font-style: italic; }
.ar-quote cite { display: block; margin-top: 0.5rem; font-size: 0.85rem; font-style: normal; color: rgb(113 113 122); }
.ar-figure { margin: 1.25rem 0; }
.ar-figure img { width: 100%; height: auto; border-radius: 0.75rem; display: block; }
.ar-figure figcaption { margin-top: 0.5rem; font-size: 0.85rem; color: rgb(113 113 122); text-align: center; }
.ar-delimiter { border: none; height: 1px; background: rgb(212 212 216); margin: 1.5rem 0; }
.ar-empty { color: rgb(161 161 170); font-style: italic; }

.article-renderer :deep(mark) { background: #fef08a; padding: 0 0.15em; border-radius: 0.15em; }
.article-renderer :deep(a) { color: rgb(59 130 246); text-decoration: underline; }
.article-renderer :deep(code) { background: rgb(244 244 245); padding: 0.1em 0.3em; border-radius: 0.25em; font-size: 0.9em; }
</style>
