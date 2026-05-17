<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeftIcon, CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  initialAnswers: { type: Object, default: () => ({}) },
  isEditing: { type: Boolean, default: false },
})
const emit = defineEmits(['complete', 'finish'])

const { t, locale } = useI18n()

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' },
  { value: 'it', label: 'Italiano' },
  { value: 'es', label: 'Español' },
  { value: 'pt', label: 'Português' },
  { value: 'ru', label: 'Русский' },
]

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

function normalizeOtherLanguages(value) {
  if (!value || value === '') return []
  if (typeof value === 'string') return value.split(',').filter(Boolean).map(lang => ({ lang: lang.trim(), level: null }))
  if (!Array.isArray(value) || value.length === 0) return []
  return typeof value[0] === 'string' ? value.map(lang => ({ lang, level: null })) : value
}

const answers = ref({
  ...props.initialAnswers,
  otherLanguages: normalizeOtherLanguages(props.initialAnswers.otherLanguages),
})

const questions = computed(() => [
  {
    id: 'language',
    type: 'choice',
    required: true,
    shortLabel: t('profile.timeline.language'),
    label: t('profile.language.label'),
    sublabel: t('profile.language.sublabel'),
    options: LANGUAGE_OPTIONS,
  },
  {
    id: 'otherLanguages',
    type: 'language-with-levels',
    required: false,
    shortLabel: t('profile.timeline.otherLanguages'),
    label: t('profile.otherLanguages.label'),
    sublabel: t('profile.otherLanguages.sublabel'),
    options: LANGUAGE_OPTIONS.filter(opt => opt.value !== answers.value.language),
  },
  {
    id: 'status',
    type: 'choice',
    required: true,
    shortLabel: t('profile.timeline.status'),
    label: t('profile.status.label'),
    sublabel: t('profile.status.sublabel'),
    options: [
      { value: 'N', label: 'Permit N' },
      { value: 'F', label: 'Permit F' },
      { value: 'S', label: 'Permit S' },
      { value: 'B', label: 'Permit B' },
      { value: 'C', label: 'Permit C' },
      { value: 'L', label: 'Permit L' },
      { value: 'G', label: 'Permit G' },
      { value: 'other', label: t('profile.status.unknown') },
    ],
  },
  {
    id: 'hasChildren',
    type: 'boolean',
    required: true,
    shortLabel: t('profile.timeline.hasChildren'),
    label: t('profile.hasChildren.label'),
    sublabel: t('profile.hasChildren.sublabel'),
  },
  {
    id: 'originSector',
    type: 'choice',
    required: false,
    shortLabel: t('profile.timeline.originSector'),
    label: t('profile.originSector.label'),
    sublabel: t('profile.originSector.sublabel'),
    options: [
      { value: 'healthcare', label: t('profile.sectors.healthcare') },
      { value: 'education', label: t('profile.sectors.education') },
      { value: 'engineering', label: t('profile.sectors.engineering') },
      { value: 'trade', label: t('profile.sectors.trade') },
      { value: 'agriculture', label: t('profile.sectors.agriculture') },
      { value: 'construction', label: t('profile.sectors.construction') },
      { value: 'it', label: t('profile.sectors.it') },
      { value: 'arts', label: t('profile.sectors.arts') },
      { value: 'administration', label: t('profile.sectors.administration') },
      { value: 'catering', label: t('profile.sectors.catering') },
      { value: 'transport', label: t('profile.sectors.transport') },
      { value: 'other', label: t('profile.sectors.other') },
    ],
  },
  {
    id: 'arrivedOverYear',
    type: 'boolean',
    required: false,
    shortLabel: t('profile.timeline.arrivedOverYear'),
    label: t('profile.arrivedOverYear.label'),
  },
  {
    id: 'birthDate',
    type: 'date',
    required: false,
    shortLabel: t('profile.timeline.birthDate'),
    label: t('profile.birthDate.label'),
    sublabel: t('profile.birthDate.sublabel'),
  },
])

const currentStep = ref(0)
const slideDirection = ref('next')
const completed = ref(false)

const question = computed(() => questions.value[currentStep.value])
const isFirst = computed(() => currentStep.value === 0)
const isLast = computed(() => currentStep.value === questions.value.length - 1)

const canAdvance = computed(() => {
  const q = question.value
  if (!q.required) return true
  const a = answers.value[q.id]
  if (q.type === 'boolean') return a === true || a === false
  return a !== undefined && a !== null && a !== ''
})

function isPassed(index) {
  return index < currentStep.value
}

function advance() {
  if (isLast.value) {
    completed.value = true
    emit('complete', answers.value)
  } else {
    slideDirection.value = 'next'
    currentStep.value++
  }
}

function select(value) {
  answers.value[question.value.id] = value
  if (question.value.id === 'language') {
    locale.value = value
    localStorage.setItem('profileLanguage', value)
  }
}

function toggle(value) {
  const current = answers.value[question.value.id] || []
  const idx = current.indexOf(value)
  answers.value[question.value.id] = idx === -1
    ? [...current, value]
    : current.filter(v => v !== value)
}

function goNext() {
  if (canAdvance.value) advance()
}

function toggleLanguage(langValue) {
  const current = answers.value[question.value.id] || []
  const idx = current.findIndex(item => item.lang === langValue)
  answers.value[question.value.id] = idx === -1
    ? [...current, { lang: langValue, level: null }]
    : current.filter((_, i) => i !== idx)
}

function isLanguageSelected(langValue) {
  return (answers.value[question.value.id] || []).some(item => item.lang === langValue)
}

function getLanguageLevel(langValue) {
  return (answers.value[question.value.id] || []).find(item => item.lang === langValue)?.level ?? null
}

function setLanguageLevel(langValue, level) {
  answers.value[question.value.id] = (answers.value[question.value.id] || []).map(item =>
    item.lang === langValue ? { ...item, level: item.level === level ? null : level } : item
  )
}

function languageLabel(langValue) {
  return LANGUAGE_OPTIONS.find(opt => opt.value === langValue)?.label ?? langValue
}


function skip() {
  const type = question.value.type
  answers.value[question.value.id] = (type === 'boolean') ? null
    : (type === 'language-with-levels') ? [] : ''
  advance()
}

function isSelected(value) {
  const a = answers.value[question.value.id]
  return question.value.type === 'multi-select' ? (a || []).includes(value) : a === value
}

function back() {
  if (!isFirst.value) {
    slideDirection.value = 'prev'
    currentStep.value--
  }
}

const activeStepEl = ref(null)

function goToStep(index) {
  if (index === currentStep.value) return
  slideDirection.value = index > currentStep.value ? 'next' : 'prev'
  currentStep.value = index
}

watch(currentStep, async () => {
  await nextTick()
  activeStepEl.value?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface-100 to-surface-200 p-6">
    <div class="w-full max-w-md lg:max-w-2xl lg:flex lg:items-start lg:gap-10">

      <!-- Desktop left column: save & exit + timeline -->
      <div v-if="!completed" class="hidden lg:flex flex-col w-40 shrink-0 pt-6">
        <button
          v-if="isEditing"
          class="flex items-center gap-1.5 text-sm text-surface-400 hover:text-surface-600 transition-colors duration-150 cursor-pointer bg-transparent border-none mb-6 self-start"
          @click="$emit('finish', answers)"
        >
          <XMarkIcon class="w-4 h-4" />
          {{ t('profile.saveExit') }}
        </button>
        <nav class="flex flex-col">
          <div v-for="(q, i) in questions" :key="q.id" class="flex items-start gap-3">
            <div class="flex flex-col items-center shrink-0">
              <button
                class="w-7 h-7 rounded-full flex items-center justify-center border-2 transition-all duration-200 cursor-pointer"
                :class="i === currentStep
                  ? 'bg-brand-600 border-brand-600'
                  : isPassed(i) ? 'bg-surface-600 border-surface-600' : 'bg-white border-surface-300'"
                @click="goToStep(i)"
              >
                <CheckIcon v-if="isPassed(i)" class="w-3.5 h-3.5 text-white" />
                <span v-else-if="i === currentStep" class="w-2 h-2 bg-white rounded-full block" />
              </button>
              <div
                v-if="i < questions.length - 1"
                class="w-0.5 h-7 my-1 transition-colors duration-300"
                :class="isPassed(i) ? 'bg-surface-400' : 'bg-surface-200'"
              />
            </div>
            <button
              class="text-sm pt-1 pb-1 text-left bg-transparent border-none cursor-pointer transition-colors duration-150 leading-tight"
              :class="i === currentStep
                ? 'text-surface-800 font-semibold'
                : isPassed(i) ? 'text-surface-500 font-medium' : 'text-surface-300'"
              @click="goToStep(i)"
            >
              {{ q.shortLabel }}
            </button>
          </div>
        </nav>
      </div>

      <!-- Mobile save & exit: above card, outside it -->
      <div v-if="isEditing && !completed" class="lg:hidden flex mb-3">
        <button
          class="flex items-center gap-1.5 text-sm text-surface-400 hover:text-surface-600 transition-colors duration-150 cursor-pointer bg-transparent border-none"
          @click="$emit('finish', answers)"
        >
          <XMarkIcon class="w-4 h-4" />
          {{ t('profile.saveExit') }}
        </button>
      </div>

      <!-- Form card -->
      <div class="bg-surface-500 rounded-2xl p-8 lg:p-10 w-full shadow-lg flex flex-col min-h-96">

        <template v-if="!completed">

          <!-- Timeline horizontale (mobile only) -->
          <div class="lg:hidden flex items-center overflow-x-auto pb-1 mb-8 -mx-2 px-2 scrollbar-none">
            <template v-for="(q, i) in questions" :key="q.id">
              <button
                :ref="i === currentStep ? (el) => { activeStepEl = el } : undefined"
                class="flex items-center gap-1.5 rounded-full border-2 transition-all duration-200 cursor-pointer shrink-0"
                :class="i === currentStep
                  ? 'bg-brand-600 border-brand-600 pl-2.5 pr-3 py-1.5'
                  : isPassed(i) ? 'bg-surface-600 border-surface-600 p-1.5' : 'bg-surface-600 border-surface-400 p-1.5'"
                @click="goToStep(i)"
              >
                <CheckIcon v-if="isPassed(i)" class="w-3.5 h-3.5 text-white shrink-0" />
                <span v-else-if="i === currentStep" class="w-2 h-2 bg-white rounded-full block shrink-0" />
                <span v-else class="w-3.5 h-3.5 flex items-center justify-center text-xs text-surface-300 font-semibold shrink-0">{{ i + 1 }}</span>
                <span v-if="i === currentStep" class="text-white text-xs font-semibold whitespace-nowrap">{{ q.shortLabel }}</span>
              </button>
              <div
                v-if="i < questions.length - 1"
                class="h-0.5 w-3 shrink-0 transition-colors duration-300 mx-0.5"
                :class="isPassed(i) ? 'bg-surface-400' : 'bg-surface-200'"
              />
            </template>
          </div>

          <Transition
            :enter-from-class="slideDirection === 'next' ? 'opacity-0 translate-x-9' : 'opacity-0 -translate-x-9'"
            enter-active-class="transition-all duration-200 ease-out"
            enter-to-class="opacity-100 translate-x-0"
            :leave-to-class="slideDirection === 'next' ? 'opacity-0 -translate-x-9' : 'opacity-0 translate-x-9'"
            leave-active-class="transition-all duration-200 ease-out"
            mode="out-in"
          >
            <div :key="currentStep" class="flex-1 flex flex-col">
              <h2 class="text-2xl font-bold text-white leading-snug mb-2">{{ question.label }}</h2>
              <p v-if="question.sublabel" class="text-sm text-surface-300 leading-relaxed mb-6">{{ question.sublabel }}</p>
              <div v-else class="mb-6" />

              <!-- Language with levels -->
              <div v-if="question.type === 'language-with-levels'" class="flex flex-col gap-4">
                <div class="grid grid-cols-2 gap-3">
                  <button
                    v-for="opt in question.options"
                    :key="opt.value"
                    class="py-3.5 px-4 border-2 rounded-xl text-sm font-medium cursor-pointer transition-all duration-150 text-left"
                    :class="isLanguageSelected(opt.value)
                      ? 'border-white bg-surface-600 text-white'
                      : 'border-surface-400 bg-surface-400 text-surface-600 hover:border-surface-200 hover:text-white'"
                    @click="toggleLanguage(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
                <div v-if="(answers[question.id] || []).length" class="flex flex-col gap-2">
                  <p class="text-xs text-surface-300 uppercase tracking-wider font-semibold">{{ t('profile.otherLanguages.levelHint') }}</p>
                  <div
                    v-for="item in (answers[question.id] || [])"
                    :key="item.lang"
                    class="flex items-center gap-2"
                  >
                    <span class="text-sm text-surface-200 w-24 shrink-0">{{ languageLabel(item.lang) }}</span>
                    <div class="flex gap-1 flex-wrap">
                      <button
                        v-for="level in CEFR_LEVELS"
                        :key="level"
                        class="px-2 py-1 rounded-lg text-xs font-semibold border cursor-pointer transition-all duration-150"
                        :class="getLanguageLevel(item.lang) === level
                          ? 'bg-surface-600 border-white text-white'
                          : 'bg-surface-400 border-surface-400 text-surface-300 hover:border-surface-200 hover:text-white'"
                        @click="setLanguageLevel(item.lang, level)"
                      >
                        {{ level }}
                      </button>
                      <button
                        class="px-2 py-1 rounded-lg text-xs font-semibold border cursor-pointer transition-all duration-150"
                        :class="getLanguageLevel(item.lang) === null
                          ? 'bg-surface-600 border-white text-white'
                          : 'bg-surface-400 border-surface-400 text-surface-300 hover:border-surface-200 hover:text-white'"
                        @click="setLanguageLevel(item.lang, null)"
                      >
                        {{ t('profile.cefrUnknown') }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Choice / Multi-select -->
              <div v-else-if="question.type === 'choice' || question.type === 'multi-select'" class="grid grid-cols-2 gap-3">
                <button
                  v-for="opt in question.options"
                  :key="opt.value"
                  class="py-3.5 px-4 border-2 rounded-xl text-sm font-medium cursor-pointer transition-all duration-150 text-left"
                  :class="isSelected(opt.value)
                    ? 'border-white bg-surface-600 text-white'
                    : 'border-surface-400 bg-surface-400 text-surface-600 hover:border-surface-200 hover:text-white'"
                  @click="question.type === 'choice' ? select(opt.value) : toggle(opt.value)"
                >
                  {{ opt.label }}
                </button>
              </div>

              <!-- Boolean -->
              <div v-else-if="question.type === 'boolean'" class="grid grid-cols-2 gap-4">
                <button
                  class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                  :class="answers[question.id] === true
                    ? 'border-white bg-surface-600 text-white'
                    : 'border-surface-400 bg-surface-400 text-surface-600 hover:border-surface-200 hover:text-white'"
                  @click="select(true)"
                >
                  {{ t('profile.yes') }}
                </button>
                <button
                  class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                  :class="answers[question.id] === false
                    ? 'border-white bg-surface-600 text-white'
                    : 'border-surface-400 bg-surface-400 text-surface-600 hover:border-surface-200 hover:text-white'"
                  @click="select(false)"
                >
                  {{ t('profile.no') }}
                </button>
              </div>

              <!-- Date -->
              <div v-else-if="question.type === 'date'">
                <input
                  type="date"
                  class="w-full border-2 border-surface-400 bg-surface-600 rounded-xl px-4 py-3 text-base text-white focus:outline-none focus:border-surface-200 transition-colors duration-150"
                  :value="answers[question.id] || ''"
                  @input="answers[question.id] = $event.target.value"
                />
              </div>
            </div>
          </Transition>

          <!-- Bottom nav -->
          <div class="mt-8 flex items-center gap-3">
            <button
              v-if="!isFirst"
              class="flex items-center gap-1 text-sm font-medium text-surface-300 hover:text-white transition-colors duration-150 cursor-pointer bg-transparent border-none p-0 shrink-0"
              @click="back"
            >
              <ArrowLeftIcon class="w-4 h-4" />{{ t('profile.back') }}
            </button>
            <div class="flex-1" />
            <button
              v-if="!question.required"
              class="text-sm text-surface-300 hover:text-surface-100 transition-colors duration-150 cursor-pointer bg-transparent border-none shrink-0"
              @click="skip"
            >
              {{ t('profile.skip') }}
            </button>
            <button
              class="px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 border-none shrink-0"
              :class="canAdvance
                ? 'bg-surface-700 text-white hover:bg-surface-800 cursor-pointer'
                : 'bg-surface-700 text-surface-500 cursor-not-allowed'"
              @click="goNext"
            >
              {{ t('profile.next') }}
            </button>
          </div>
        </template>

        <!-- Done -->
        <template v-else>
          <div class="flex-1 flex flex-col items-center justify-center text-center gap-3 py-6">
            <div class="w-16 h-16 bg-surface-600 text-white rounded-full flex items-center justify-center mb-2">
              <CheckIcon class="w-8 h-8" />
            </div>
            <h2 class="text-2xl font-bold text-white">{{ t('profile.done.title') }}</h2>
            <p class="text-sm text-surface-300">{{ t('profile.done.subtitle') }}</p>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>
