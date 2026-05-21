<script setup>
import { ref, computed, onMounted } from 'vue'
import { SparklesIcon, Squares2X2Icon, ListBulletIcon } from '@heroicons/vue/24/outline'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const show = ref(false)
const step = ref(0)
const STORAGE_KEY = 'pin_tutorial_v1'

const steps = computed(() => [
  {
    icon: Squares2X2Icon,
    iconBg: 'bg-surface-100',
    iconColor: 'text-surface-600',
    title: t('tutorial.step1Title'),
    body: t('tutorial.step1Body'),
  },
  {
    icon: SparklesIcon,
    iconBg: 'bg-brand-50',
    iconColor: 'text-brand-500',
    title: t('tutorial.step2Title'),
    body: t('tutorial.step2Body'),
  },
  {
    icon: ListBulletIcon,
    iconBg: 'bg-surface-100',
    iconColor: 'text-surface-500',
    title: t('tutorial.step3Title'),
    body: t('tutorial.step3Body'),
  },
])

onMounted(() => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    setTimeout(() => { show.value = true }, 400)
  }
})

function next() {
  if (step.value < steps.value.length - 1) step.value++
  else done()
}

function done() {
  localStorage.setItem(STORAGE_KEY, '1')
  show.value = false
}
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <!-- backdrop -->
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="done" />

      <!-- sheet / modal -->
      <Transition name="sheet" appear>
        <div
          v-if="show"
          class="relative bg-white w-full sm:max-w-sm sm:mx-4 rounded-t-3xl sm:rounded-2xl shadow-2xl overflow-hidden"
        >
          <!-- mobile handle -->
          <div class="w-10 h-1 bg-surface-200 rounded-full mx-auto mt-3 mb-0 sm:hidden" />

          <div class="px-6 pb-8 pt-5 sm:p-8">
            <!-- step dots -->
            <div class="flex gap-1.5 justify-center mb-7">
              <div
                v-for="(_, i) in steps"
                :key="i"
                class="h-1.5 rounded-full transition-all duration-300"
                :class="i === step ? 'w-6 bg-brand-500' : 'w-1.5 bg-surface-200'"
              />
            </div>

            <!-- icon -->
            <div
              class="w-16 h-16 rounded-2xl mx-auto mb-5 flex items-center justify-center transition-colors duration-300"
              :class="steps[step].iconBg"
            >
              <component :is="steps[step].icon" class="w-8 h-8 transition-colors duration-300" :class="steps[step].iconColor" />
            </div>

            <!-- visual mockup per step -->
            <div class="mb-5 px-1">
              <!-- Step 1: category pills mockup -->
              <div v-if="step === 0" class="flex flex-wrap gap-2 justify-center">
                <span class="px-3 py-1.5 bg-brand-100 text-brand-700 rounded-full text-xs font-semibold">Santé</span>
                <span class="px-3 py-1.5 bg-brand-100 text-brand-700 rounded-full text-xs font-semibold">Logement</span>
                <span class="px-3 py-1.5 bg-surface-100 text-surface-500 rounded-full text-xs font-semibold">Travail</span>
                <span class="px-3 py-1.5 bg-surface-100 text-surface-500 rounded-full text-xs font-semibold">Éducation</span>
              </div>

              <!-- Step 2: recommended resource mockup -->
              <div v-else-if="step === 1" class="bg-brand-50 border border-brand-200 rounded-xl p-3.5 text-left">
                <p class="text-xs font-semibold text-brand-500 flex items-center gap-1 mb-1.5">
                  <SparklesIcon class="w-3.5 h-3.5" />
                  Recommandé
                </p>
                <p class="text-sm font-semibold text-surface-800 leading-snug">L'assurance maladie</p>
                <p class="text-xs text-surface-500 mt-0.5">Toute personne en Suisse doit s'inscrire…</p>
              </div>

              <!-- Step 3: other resource mockup -->
              <div v-else class="space-y-2">
                <div class="bg-surface-50 border border-surface-200 rounded-xl p-3.5 text-left">
                  <p class="text-sm font-semibold text-surface-700 leading-snug">Formation professionnelle</p>
                  <p class="text-xs text-surface-400 mt-0.5">Obtenir un diplôme suisse en tant qu'adulte…</p>
                </div>
                <div class="bg-surface-50 border border-surface-200 rounded-xl p-3.5 text-left">
                  <p class="text-sm font-semibold text-surface-700 leading-snug">Faire reconnaître ses diplômes</p>
                  <p class="text-xs text-surface-400 mt-0.5">Valider en Suisse un diplôme étranger…</p>
                </div>
              </div>
            </div>

            <!-- text -->
            <h2 class="text-lg font-bold text-center text-surface-900 mb-2">{{ steps[step].title }}</h2>
            <p class="text-surface-500 text-center leading-relaxed text-sm">{{ steps[step].body }}</p>

            <!-- buttons -->
            <button
              class="mt-6 w-full py-3 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-semibold text-sm transition-colors cursor-pointer border-none"
              @click="next"
            >
              {{ step < steps.length - 1 ? t('tutorial.next') : t('tutorial.finish') }}
            </button>
            <button
              class="mt-2 w-full text-sm text-surface-400 hover:text-surface-600 py-2 bg-transparent border-none cursor-pointer transition-colors"
              @click="done"
            >
              {{ t('tutorial.skip') }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.sheet-enter-active { transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.25s ease; }
.sheet-leave-active { transition: transform 0.25s ease-in, opacity 0.2s ease; }
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); opacity: 0; }

@media (min-width: 640px) {
  .sheet-enter-from, .sheet-leave-to { transform: scale(0.96) translateY(0); opacity: 0; }
}
</style>
