<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeftIcon, CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  initialAnswers: { type: Object, default: () => ({}) },
  isEditing: { type: Boolean, default: false },
})
const emit = defineEmits(['complete', 'languageChange', 'finish'])

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

const answers = ref({
  ...props.initialAnswers,
  otherLanguages: props.initialAnswers.otherLanguages || [],
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
    type: 'multi-select',
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
    emit('languageChange', value)
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

function skip() {
  answers.value[question.value.id] = question.value.type === 'boolean' ? null : ''
  advance()
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
      <div class="bg-white rounded-2xl p-8 lg:p-10 w-full shadow-lg flex flex-col min-h-96">

        <template v-if="!completed">

          <!-- Timeline horizontale (mobile only) -->
          <div class="lg:hidden flex items-center overflow-x-auto pb-1 mb-8 -mx-2 px-2 scrollbar-none">
            <template v-for="(q, i) in questions" :key="q.id">
              <button
                :ref="i === currentStep ? (el) => { activeStepEl = el } : undefined"
                class="flex items-center gap-1.5 rounded-full border-2 transition-all duration-200 cursor-pointer shrink-0"
                :class="i === currentStep
                  ? 'bg-brand-600 border-brand-600 pl-2.5 pr-3 py-1.5'
                  : isPassed(i) ? 'bg-surface-600 border-surface-600 p-1.5' : 'bg-white border-surface-200 p-1.5'"
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
              <h2 class="text-2xl font-bold text-surface-800 leading-snug mb-2">{{ question.label }}</h2>
              <p v-if="question.sublabel" class="text-sm text-gray-500 leading-relaxed mb-6">{{ question.sublabel }}</p>
              <div v-else class="mb-6" />

              <!-- Single choice -->
              <div v-if="question.type === 'choice'" class="grid grid-cols-2 gap-3">
                <button
                  v-for="opt in question.options"
                  :key="opt.value"
                  class="py-3.5 px-4 border-2 rounded-xl text-sm font-medium cursor-pointer transition-all duration-150 text-left"
                  :class="answers[question.id] === opt.value
                    ? 'border-surface-600 bg-surface-600 text-white'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-surface-300 hover:bg-surface-50 hover:text-surface-700'"
                  @click="select(opt.value)"
                >
                  {{ opt.label }}
                </button>
              </div>

              <!-- Multi-select -->
              <div v-else-if="question.type === 'multi-select'" class="grid grid-cols-2 gap-3">
                <button
                  v-for="opt in question.options"
                  :key="opt.value"
                  class="py-3.5 px-4 border-2 rounded-xl text-sm font-medium cursor-pointer transition-all duration-150 text-left"
                  :class="(answers[question.id] || []).includes(opt.value)
                    ? 'border-surface-600 bg-surface-600 text-white'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-surface-300 hover:bg-surface-50 hover:text-surface-700'"
                  @click="toggle(opt.value)"
                >
                  {{ opt.label }}
                </button>
              </div>

              <!-- Boolean -->
              <div v-else-if="question.type === 'boolean'" class="grid grid-cols-2 gap-4">
                <button
                  class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                  :class="answers[question.id] === true
                    ? 'border-surface-600 bg-surface-600 text-white'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-surface-600 hover:bg-surface-600 hover:text-white'"
                  @click="select(true)"
                >
                  {{ t('profile.yes') }}
                </button>
                <button
                  class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                  :class="answers[question.id] === false
                    ? 'border-surface-600 bg-surface-600 text-white'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-surface-600 hover:bg-surface-600 hover:text-white'"
                  @click="select(false)"
                >
                  {{ t('profile.no') }}
                </button>
              </div>

              <!-- Date -->
              <div v-else-if="question.type === 'date'">
                <input
                  type="date"
                  class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-base text-surface-800 focus:outline-none focus:border-surface-600 transition-colors duration-150"
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
              class="flex items-center gap-1 text-sm font-medium text-surface-400 hover:text-surface-700 transition-colors duration-150 cursor-pointer bg-transparent border-none p-0 shrink-0"
              @click="back"
            >
              <ArrowLeftIcon class="w-4 h-4" />{{ t('profile.back') }}
            </button>
            <div class="flex-1" />
            <button
              v-if="!question.required"
              class="text-sm text-surface-400 hover:text-surface-500 transition-colors duration-150 cursor-pointer bg-transparent border-none shrink-0"
              @click="skip"
            >
              {{ t('profile.skip') }}
            </button>
            <button
              class="px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 border-none shrink-0"
              :class="canAdvance
                ? 'bg-surface-700 text-white hover:bg-surface-800 cursor-pointer'
                : 'bg-surface-100 text-surface-300 cursor-not-allowed'"
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
            <h2 class="text-2xl font-bold text-surface-800">{{ t('profile.done.title') }}</h2>
            <p class="text-sm text-gray-500">{{ t('profile.done.subtitle') }}</p>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>
