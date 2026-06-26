import { ref } from 'vue'

// Short resource language codes -> BCP-47 tags the speech engine understands.
const LANG_MAP = {
  fr: 'fr-FR', uk: 'uk-UA', ru: 'ru-RU', en: 'en-GB',
}

export function stripHtml(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return doc.body.textContent || ''
}

// Chrome stops long utterances after a few seconds, so we read sentence-sized chunks.
function chunkText(text, max = 200) {
  const out = []
  let buf = ''
  for (const sentence of text.split(/(?<=[.!?。])\s+/)) {
    if (buf && (buf + ' ' + sentence).length > max) { out.push(buf); buf = sentence }
    else buf = buf ? buf + ' ' + sentence : sentence
  }
  if (buf) out.push(buf)
  return out
}

// Shared singleton state: only one block speaks at a time across the whole page,
// and speakingId identifies which button is currently active.
const supported = typeof window !== 'undefined' && 'speechSynthesis' in window
const speakingId = ref(null)

function stop() {
  if (!supported) return
  window.speechSynthesis.cancel()
  speakingId.value = null
}

// Among the voices that match the language, pick the most natural-sounding one.
// Online voices (Google, Microsoft Natural, Apple enhanced…) sound far better
// than the default offline engine, so we score and prefer them.
function pickVoice(voices, lang, bcp) {
  const short = (lang || 'fr')
  const candidates = voices.filter(v => {
    const l = (v.lang || '').replace('_', '-')
    return l === bcp || l.toLowerCase().startsWith(short)
  })
  if (!candidates.length) return null
  const score = (v) => {
    let s = 0
    const n = (v.name || '').toLowerCase()
    if (!v.localService) s += 4
    if (/google|natural|neural|enhanced|premium|wavenet|siri/.test(n)) s += 3
    if (v.default) s += 1
    return s
  }
  return [...candidates].sort((a, b) => score(b) - score(a))[0]
}

function speak(id, text, lang) {
  if (!supported) return
  window.speechSynthesis.cancel()
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  if (!clean) return
  const bcp = LANG_MAP[lang] || lang || 'fr-FR'
  const voice = pickVoice(window.speechSynthesis.getVoices(), lang, bcp)
  const chunks = chunkText(clean)
  speakingId.value = id
  chunks.forEach((part, i) => {
    const u = new SpeechSynthesisUtterance(part)
    u.lang = bcp
    if (voice) u.voice = voice
    if (i === chunks.length - 1) u.onend = () => { if (speakingId.value === id) speakingId.value = null }
    u.onerror = () => { if (speakingId.value === id) speakingId.value = null }
    window.speechSynthesis.speak(u)
  })
}

function toggle(id, text, lang) {
  if (speakingId.value === id) stop()
  else speak(id, text, lang)
}

export function useSpeech() {
  return { supported, speakingId, toggle, stop }
}
