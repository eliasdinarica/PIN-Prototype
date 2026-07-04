import { ref } from 'vue'

// Audio is synthesised on the server (see backend `pin_prototype/tts.py`) and
// returned as an MP3 the browser just plays. This is why it now sounds the same
// on every device: it no longer depends on voices installed on the visitor's
// machine (which is what made Ukrainian silent before).
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function stripHtml(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return doc.body.textContent || ''
}

// Shared singleton state: only one block plays at a time across the whole page,
// and speakingId identifies which button is currently active.
const supported = typeof window !== 'undefined' && 'Audio' in window
const speakingId = ref(null)

let audio = null
let currentUrl = null
// Bumped on every stop()/new play so a slow fetch that resolves late can tell it
// has been superseded and must not start playing.
let token = 0

function teardown() {
  if (audio) {
    audio.onended = audio.onerror = null
    try { audio.pause() } catch { /* ignore */ }
    audio = null
  }
  if (currentUrl) {
    URL.revokeObjectURL(currentUrl)
    currentUrl = null
  }
}

function stop() {
  token++
  teardown()
  speakingId.value = null
}

async function speak(id, text, lang) {
  if (!supported) return
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  if (!clean) return
  stop()
  const mine = ++token
  speakingId.value = id
  try {
    const resp = await fetch(`${API}/api/tts/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, lang: lang || 'fr' }),
    })
    if (!resp.ok) throw new Error(`tts ${resp.status}`)
    const blob = await resp.blob()
    if (mine !== token) return // stopped or replaced while fetching
    currentUrl = URL.createObjectURL(blob)
    audio = new Audio(currentUrl)
    audio.onended = () => { if (mine === token) stop() }
    audio.onerror = () => { if (mine === token) stop() }
    await audio.play()
  } catch {
    if (mine === token) { teardown(); speakingId.value = null }
  }
}

function toggle(id, text, lang) {
  if (speakingId.value === id) stop()
  else speak(id, text, lang)
}

export function useSpeech() {
  return { supported, speakingId, toggle, stop }
}
