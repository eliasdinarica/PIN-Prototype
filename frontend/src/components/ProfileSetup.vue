<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeftIcon, CheckIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  initialAnswers: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['complete', 'languageChange'])

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
    autoAdvance: true,
    label: t('profile.language.label'),
    sublabel: t('profile.language.sublabel'),
    options: LANGUAGE_OPTIONS,
  },
  {
    id: 'otherLanguages',
    type: 'multi-select',
    label: t('profile.otherLanguages.label'),
    sublabel: t('profile.otherLanguages.sublabel'),
    options: LANGUAGE_OPTIONS.filter(opt => opt.value !== answers.value.language),
  },
  {
    id: 'status',
    type: 'choice',
    autoAdvance: true,
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
    autoAdvance: true,
    label: t('profile.hasChildren.label'),
    sublabel: t('profile.hasChildren.sublabel'),
  },
  {
    id: 'originSector',
    type: 'choice',
    autoAdvance: true,
    optional: true,
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
    autoAdvance: true,
    optional: true,
    label: t('profile.arrivedOverYear.label'),
  },
  {
    id: 'birthDate',
    type: 'date',
    optional: true,
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
const progressPct = computed(() => Math.round(((currentStep.value + 1) / questions.value.length) * 100))

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

  if (question.value.autoAdvance) {
    advance()
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
  advance()
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
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface-100 to-surface-200 p-6">
    <div class="bg-white rounded-2xl p-10 w-full max-w-md shadow-lg flex flex-col min-h-96">

      <template v-if="!completed">
        <!-- Progress -->
        <div class="h-1 bg-surface-200 rounded-full overflow-hidden mb-2">
          <div
            class="h-full bg-surface-600 rounded-full transition-all duration-300"
            :style="{ width: progressPct + '%' }"
          />
        </div>
        <p class="text-xs font-semibold tracking-wider uppercase text-surface-500 mb-8">
          {{ t('profile.step', { current: currentStep + 1, total: questions.length }) }}
        </p>

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
            <p v-if="question.sublabel" class="text-sm text-gray-500 leading-relaxed mb-8">{{ question.sublabel }}</p>
            <div v-else class="mb-8" />

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
              <button
                v-if="question.optional"
                class="col-span-2 mt-2 py-2 text-sm text-surface-400 hover:text-surface-600 transition-colors duration-150 cursor-pointer bg-transparent border-none"
                @click="skip"
              >
                {{ t('profile.skip') }}
              </button>
            </div>

            <!-- Multi-select -->
            <div v-else-if="question.type === 'multi-select'" class="flex flex-col gap-3">
              <div class="grid grid-cols-2 gap-3">
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
              <button
                class="mt-3 w-full py-3.5 rounded-xl bg-surface-700 text-white font-semibold text-sm cursor-pointer hover:bg-surface-800 transition-colors duration-150 border-none"
                @click="goNext"
              >
                {{ t('profile.next') }}
              </button>
            </div>

            <!-- Boolean -->
            <div v-else-if="question.type === 'boolean'" class="flex flex-col gap-4">
              <div class="grid grid-cols-2 gap-4">
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
              <button
                v-if="question.optional"
                class="py-2 text-sm text-surface-400 hover:text-surface-600 transition-colors duration-150 cursor-pointer bg-transparent border-none"
                @click="skip"
              >
                {{ t('profile.skip') }}
              </button>
            </div>

            <!-- Date -->
            <div v-else-if="question.type === 'date'" class="flex flex-col gap-3">
              <input
                type="date"
                class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-base text-surface-800 focus:outline-none focus:border-surface-600 transition-colors duration-150"
                :value="answers[question.id] || ''"
                @input="answers[question.id] = $event.target.value"
              />
              <button
                class="w-full py-3.5 rounded-xl bg-surface-700 text-white font-semibold text-sm cursor-pointer hover:bg-surface-800 transition-colors duration-150 border-none"
                @click="goNext"
              >
                {{ t('profile.next') }}
              </button>
              <button
                class="py-2 text-sm text-surface-400 hover:text-surface-600 transition-colors duration-150 cursor-pointer bg-transparent border-none"
                @click="skip"
              >
                {{ t('profile.skip') }}
              </button>
            </div>
          </div>
        </Transition>

        <button
          v-if="!isFirst"
          class="mt-6 self-start text-sm font-medium text-surface-500 hover:text-surface-700 transition-colors duration-150 cursor-pointer bg-transparent border-none p-0"
          @click="back"
        >
          <ArrowLeftIcon class="w-4 h-4 inline mr-1" />{{ t('profile.back') }}
        </button>
      </template>

      <!-- Done -->
      <template v-else>
        <div class="flex-1 flex flex-col items-center justify-center text-center gap-3">
          <div class="w-16 h-16 bg-surface-600 text-white rounded-full flex items-center justify-center mb-2">
            <CheckIcon class="w-8 h-8" />
          </div>
          <h2 class="text-2xl font-bold text-surface-800">{{ t('profile.done.title') }}</h2>
          <p class="text-sm text-gray-500">{{ t('profile.done.subtitle') }}</p>
        </div>
      </template>

    </div>
  </div>
</template>
