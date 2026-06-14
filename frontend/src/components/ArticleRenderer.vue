<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  // Fixed sections: [{ key: 'why'|'how'|'location', html: '...' }]
  sections: { type: Array, default: () => [] },
})

// Collapsed by default — user opens each item via the "+".
const open = ref({})
function toggle(key) {
  open.value = { ...open.value, [key]: !open.value[key] }
}

const SAFE_IFRAME_ATTRS = new Set(['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow', 'title', 'loading'])

function sanitizeHtml(html) {
  if (!html) return ''
  const ALLOWED = new Set(['b', 'strong', 'i', 'em', 'u', 'mark', 'a', 'br', 'code', 'p',
    'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'blockquote', 'hr', 'img', 'figure', 'figcaption', 'div', 'iframe'])
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, 'text/html')
  const walk = (node) => {
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType !== Node.ELEMENT_NODE) continue
      const tag = child.tagName.toLowerCase()
      if (!ALLOWED.has(tag)) {
        child.replaceWith(document.createTextNode(child.textContent || ''))
        continue
      }
      for (const attr of Array.from(child.attributes)) {
        const n = attr.name
        if (tag === 'a' && n === 'href') {
          const v = attr.value.trim().toLowerCase()
          if (v.startsWith('javascript:') || v.startsWith('data:')) child.removeAttribute(n)
          continue
        }
        if (tag === 'img' && (n === 'src' || n === 'alt' || n === 'width' || n === 'height')) continue
        if (tag === 'iframe' && SAFE_IFRAME_ATTRS.has(n)) continue
        if (tag === 'div' && n === 'class') continue
        child.removeAttribute(n)
      }
      if (tag === 'a') { child.setAttribute('target', '_blank'); child.setAttribute('rel', 'noopener noreferrer') }
      walk(child)
    }
  }
  walk(doc.body.firstChild)
  return doc.body.firstChild.innerHTML
}

// Split a section's HTML into an intro (before the first heading) and a list of
// collapsible items (each heading + the content that follows it).
function parseSection(html) {
  const doc = new DOMParser().parseFromString(`<div>${html || ''}</div>`, 'text/html')
  const root = doc.body.firstChild
  const intro = []
  const items = []
  let current = null
  for (const node of Array.from(root.childNodes)) {
    const isHeading = node.nodeType === Node.ELEMENT_NODE && /^H[1-3]$/.test(node.tagName)
    if (isHeading) {
      current = { title: node.textContent || '', html: '' }
      items.push(current)
    } else {
      const frag = node.nodeType === Node.ELEMENT_NODE ? node.outerHTML : (node.textContent || '')
      if (current) current.html += frag
      else intro.push(frag)
    }
  }
  return { intro: intro.join('').trim(), items }
}

const parsedSections = computed(() =>
  props.sections.map(s => ({
    key: s.key,
    title: t(`article.${s.key}`),
    ...parseSection(s.html),
  }))
)
</script>

<template>
  <div class="ar">
    <section v-for="s in parsedSections" :key="s.key" class="ar-card">
      <h2 class="ar-title">{{ s.title }}</h2>

      <!-- Intro (text before the first heading) -->
      <div v-if="s.intro" class="ar-rt ar-intro" v-html="sanitizeHtml(s.intro)" />

      <!-- Collapsible item rows -->
      <div v-if="s.items.length" class="ar-items">
        <div v-for="(item, i) in s.items" :key="i" class="ar-item">
          <button
            class="ar-item-head"
            :aria-expanded="!!open[`${s.key}-${i}`]"
            @click="toggle(`${s.key}-${i}`)"
          >
            <span class="ar-item-title">{{ item.title }}</span>
            <span class="ar-plus">{{ open[`${s.key}-${i}`] ? '–' : '+' }}</span>
          </button>
          <div
            v-if="open[`${s.key}-${i}`]"
            class="ar-rt ar-item-body"
            v-html="sanitizeHtml(item.html)"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ar { display: flex; flex-direction: column; gap: 0.75rem; }

.ar-card {
  background: #fff;
  border-radius: 1rem;
  border: 1px solid rgb(241 245 249);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 1.5rem 1.5rem 0.5rem;
}
.ar-title {
  font-size: 1.5rem; font-weight: 700; color: rgb(15 23 42);
  line-height: 1.2; margin-bottom: 1rem;
}
.ar-intro { color: rgb(63 63 70); margin-bottom: 0.75rem; }

/* collapsible item rows — thin bands with a + */
.ar-item { border-top: 1px solid rgb(229 231 235); }
.ar-item:last-child { border-bottom: 1px solid rgb(229 231 235); }
.ar-item-head {
  width: 100%;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 0.95rem 0.25rem;
  background: none; border: none; cursor: pointer;
  text-align: left;
}
.ar-item-title { font-size: 0.95rem; font-weight: 500; color: rgb(31 41 55); line-height: 1.4; }
.ar-plus { font-size: 1.4rem; line-height: 1; color: rgb(148 163 184); flex-shrink: 0; width: 1.25rem; text-align: center; }
.ar-item-body { padding: 0 0.25rem 1rem; color: rgb(63 63 70); }

/* richtext typography */
.ar-rt :deep(h1) { font-size: 1.2rem; font-weight: 700; color: rgb(24 24 27); margin: 1rem 0 0.5rem; }
.ar-rt :deep(h2) { font-size: 1.05rem; font-weight: 700; color: rgb(24 24 27); margin: 0.9rem 0 0.45rem; }
.ar-rt :deep(h3) { font-size: 0.95rem; font-weight: 700; color: rgb(39 39 42); margin: 0.8rem 0 0.4rem; }
.ar-rt :deep(p)  { font-size: 0.95rem; line-height: 1.65; margin: 0 0 0.75rem; }
.ar-rt :deep(ul),
.ar-rt :deep(ol) { margin: 0 0 0.75rem 1.25rem; line-height: 1.65; }
.ar-rt :deep(li) { margin-bottom: 0.25rem; }
.ar-rt :deep(ul) { list-style: disc; }
.ar-rt :deep(ol) { list-style: decimal; }
.ar-rt :deep(blockquote) { border-left: 3px solid rgb(212 212 216); padding: 0.25rem 0.75rem; color: rgb(82 82 91); font-style: italic; margin: 0.75rem 0; }
.ar-rt :deep(hr) { border: none; height: 1px; background: rgb(212 212 216); margin: 1rem 0; }
.ar-rt :deep(a)  { color: rgb(59 130 246); text-decoration: underline; }
.ar-rt :deep(b), .ar-rt :deep(strong) { font-weight: 600; }
.ar-rt :deep(mark) { background: #fef08a; padding: 0 0.15em; border-radius: 0.15em; }
.ar-rt :deep(code) { background: rgb(244 244 245); padding: 0.1em 0.3em; border-radius: 0.25em; font-size: 0.9em; }
.ar-rt :deep(img)  { max-width: 100%; border-radius: 0.5rem; display: block; margin: 0.5rem 0; }
.ar-rt :deep(.responsive-object) { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 0.5rem; margin: 0.5rem 0; }
.ar-rt :deep(.responsive-object iframe) { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }
</style>
