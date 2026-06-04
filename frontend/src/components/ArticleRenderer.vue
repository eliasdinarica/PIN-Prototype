<script setup>
const props = defineProps({
  body: { type: Array, default: () => [] },
})

// Blocks are now a flat array: [{type, value}, ...]
// richtext  → value is HTML string (already expanded by backend)
// image     → value is {url, alt, width, height}
// embed     → value is {url, html}
// columns   → value is {left: html, right: html}
// callout   → value is {text: html}

const SAFE_IFRAME_ATTRS = new Set(['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow', 'title', 'loading'])

function sanitizeHtml(html) {
  if (!html) return ''
  const ALLOWED = new Set(['b', 'strong', 'i', 'em', 'u', 'mark', 'a', 'br', 'code', 'p',
    'h2', 'h3', 'ul', 'ol', 'li', 'blockquote', 'hr', 'img', 'figure', 'figcaption', 'div', 'iframe'])
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
        child.removeAttribute(n)
      }
      if (tag === 'a') { child.setAttribute('target', '_blank'); child.setAttribute('rel', 'noopener noreferrer') }
      walk(child)
    }
  }
  walk(doc.body.firstChild)
  return doc.body.firstChild.innerHTML
}
</script>

<template>
  <article class="ar">
    <template v-for="(block, i) in body" :key="i">

      <div v-if="block.type === 'richtext'"
           class="ar-rt"
           v-html="sanitizeHtml(block.value)" />

      <figure v-else-if="block.type === 'image'" class="ar-figure">
        <img :src="block.value.url" :alt="block.value.alt || ''" :width="block.value.width" :height="block.value.height" />
      </figure>

      <div v-else-if="block.type === 'embed' && block.value.html"
           class="ar-embed"
           v-html="sanitizeHtml(block.value.html)" />

      <div v-else-if="block.type === 'columns'" class="ar-columns">
        <div class="ar-col ar-rt" v-html="sanitizeHtml(block.value.left)" />
        <div class="ar-col ar-rt" v-html="sanitizeHtml(block.value.right)" />
      </div>

      <div v-else-if="block.type === 'callout'" class="ar-callout ar-rt" v-html="sanitizeHtml(block.value.text)" />

    </template>

    <p v-if="!body || !body.length" class="ar-empty">No content yet.</p>
  </article>
</template>

<style scoped>
.ar { color: rgb(63 63 70); overflow-x: hidden; max-width: 100%; }

/* richtext typography */
.ar-rt :deep(h2) { font-size: 1.2rem; font-weight: 700; color: rgb(24 24 27); margin: 1.4rem 0 0.6rem; }
.ar-rt :deep(h3) { font-size: 1rem; font-weight: 700; color: rgb(39 39 42); margin: 1.1rem 0 0.5rem; }
.ar-rt :deep(p)  { font-size: 1rem; line-height: 1.65; margin: 0 0 0.85rem; }
.ar-rt :deep(ul),
.ar-rt :deep(ol) { margin: 0 0 0.85rem 1.25rem; line-height: 1.65; }
.ar-rt :deep(li) { margin-bottom: 0.25rem; }
.ar-rt :deep(ul) { list-style: disc; }
.ar-rt :deep(ol) { list-style: decimal; }
.ar-rt :deep(blockquote) { border-left: 3px solid rgb(212 212 216); padding: 0.25rem 0.75rem; color: rgb(82 82 91); font-style: italic; margin: 0.75rem 0; }
.ar-rt :deep(hr) { border: none; height: 1px; background: rgb(212 212 216); margin: 1.25rem 0; }
.ar-rt :deep(a)  { color: rgb(59 130 246); text-decoration: underline; }
.ar-rt :deep(b), .ar-rt :deep(strong) { font-weight: 600; }
.ar-rt :deep(mark) { background: #fef08a; padding: 0 0.15em; border-radius: 0.15em; }
.ar-rt :deep(code) { background: rgb(244 244 245); padding: 0.1em 0.3em; border-radius: 0.25em; font-size: 0.9em; }
.ar-rt :deep(img)  { max-width: 100%; border-radius: 0.5rem; display: block; margin: 0.5rem 0; }

/* image block */
.ar-figure { margin: 1rem 0; }
.ar-figure img { width: 100%; height: auto; border-radius: 0.75rem; display: block; }

/* embed block */
.ar-embed { margin: 1rem 0; border-radius: 0.75rem; overflow: hidden; }
.ar-embed :deep(iframe) { width: 100%; aspect-ratio: 16/9; display: block; border: none; }

/* two-column layout */
.ar-columns { display: flex; flex-wrap: wrap; gap: 1rem; margin: 0.75rem 0; }
.ar-col { flex: 1 1 240px; min-width: 0; background: rgb(248 248 250); border-radius: 0.75rem; padding: 0.875rem; }

/* callout */
.ar-callout {
  background: rgb(239 246 255); border-left: 4px solid rgb(59 130 246);
  border-radius: 0.5rem; padding: 0.75rem 1rem; margin: 0.75rem 0;
}

.ar-empty { color: rgb(161 161 170); font-style: italic; }
</style>
