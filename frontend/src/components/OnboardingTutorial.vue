<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const show = ref(false)
const STORAGE_KEY = 'pin_tutorial_v1'

// Positions calculées dynamiquement depuis le DOM
const style1 = ref({})
const style2 = ref({})
const arrow1 = ref('up')   // 'up' | 'left' | 'down'
const arrow2 = ref('up')

function place() {
  const desktop = window.innerWidth >= 1024
  const HINT_W = 196

  if (desktop) {
    const cats = document.querySelector('[data-tut="cats-desktop"]')
    const res  = document.querySelector('[data-tut="res"]')

    if (cats) {
      const r = cats.getBoundingClientRect()
      // Bulle à droite de la sidebar, flèche ← vers la sidebar
      style1.value = {
        top:  `${r.top + 40}px`,
        left: `${r.right + 14}px`,
      }
      arrow1.value = 'left'
    }

    if (res) {
      const r = res.getBoundingClientRect()
      // Bulle au-dessus du premier card (décalée à droite), flèche ↓ vers les cartes
      const leftPos = Math.min(r.left + r.width * 0.55, window.innerWidth - HINT_W - 16)
      style2.value = {
        top:  `${r.top - 10}px`,
        left: `${leftPos}px`,
      }
      arrow2.value = 'up'
    }

  } else {
    const cats = document.querySelector('[data-tut="cats-mobile"]')
    const res  = document.querySelector('[data-tut="res"]')

    if (cats) {
      const r = cats.getBoundingClientRect()
      // Bulle juste sous la barre de pills, flèche ↑ vers les pills
      style1.value = {
        top:  `${r.bottom + 8}px`,
        left: '12px',
      }
      arrow1.value = 'up'
    }

    if (res) {
      const r = res.getBoundingClientRect()
      // Bulle à droite dans la zone des cartes, flèche ↑
      const leftPos = Math.min(r.right - HINT_W - 8, window.innerWidth - HINT_W - 12)
      style2.value = {
        top:  `${r.top + 24}px`,
        left: `${Math.max(leftPos, 12)}px`,
      }
      arrow2.value = 'up'
    }
  }
}

onMounted(() => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    // Délai pour laisser le DOM se rendre, puis on mesure
    setTimeout(() => {
      place()
      show.value = true
    }, 800)
  }
})

function done() {
  localStorage.setItem(STORAGE_KEY, '1')
  show.value = false
}
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-40 pointer-events-none">

      <!-- Couche de fermeture -->
      <div class="absolute inset-0 pointer-events-auto" @click="done" />

      <!-- Bulle 1 : catégories -->
      <div class="hint pointer-events-auto" :style="style1" @click.stop="done">
        <div class="tri" :class="`tri-${arrow1}`" />
        <p>{{ t('tutorial.hintCategories') }}</p>
      </div>

      <!-- Bulle 2 : ressources -->
      <div class="hint pointer-events-auto" :style="style2" @click.stop="done">
        <div class="tri" :class="`tri-${arrow2}`" />
        <p>{{ t('tutorial.hintResources') }}</p>
      </div>

      <p class="absolute bottom-8 inset-x-0 text-center text-white/40 text-xs pointer-events-none select-none">
        {{ t('tutorial.tapToDismiss') }}
      </p>

    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active { transition: opacity 0.35s ease; }
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.hint {
  position: fixed;
  background: white;
  border-radius: 12px;
  padding: 11px 14px;
  width: 196px;
  font-size: 13px;
  font-weight: 500;
  color: rgb(24 24 27);
  line-height: 1.45;
  box-shadow: 0 4px 20px rgba(0,0,0,0.28);
}

/* Triangles CSS (flèches) */
.tri { position: absolute; width: 0; height: 0; }

/* ↑ flèche en haut à gauche */
.tri-up {
  top: -9px; left: 18px;
  border-left: 9px solid transparent;
  border-right: 9px solid transparent;
  border-bottom: 9px solid white;
}

/* ← flèche à gauche */
.tri-left {
  left: -9px; top: 16px;
  border-top: 9px solid transparent;
  border-bottom: 9px solid transparent;
  border-right: 9px solid white;
}

/* ↓ flèche en bas */
.tri-down {
  bottom: -9px; left: 18px;
  border-left: 9px solid transparent;
  border-right: 9px solid transparent;
  border-top: 9px solid white;
}
</style>
