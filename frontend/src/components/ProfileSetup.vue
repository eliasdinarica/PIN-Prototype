<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeftIcon, CheckIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  initialAnswers: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['complete', 'languageChange'])

const { t, locale } = useI18n()

const questions = computed(() => [
  {
    id: 'language',
    type: 'choice',
    label: t('profile.language.label'),
    sublabel: t('profile.language.sublabel'),
    options: [
      { value: 'en', label: 'English' },
      { value: 'fr', label: 'Français' },
      { value: 'de', label: 'Deutsch' },
      { value: 'it', label: 'Italiano' },
      { value: 'es', label: 'Español' },
      { value: 'pt', label: 'Português' },
      { value: 'ru', label: 'Русский' },
    ],
  },
  {
    id: 'status',
    type: 'choice',
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
    label: t('profile.hasChildren.label'),
    sublabel: t('profile.hasChildren.sublabel'),
  },
])

const currentStep = ref(0)
const slideDirection = ref('next')
const answers = ref({ ...props.initialAnswers })
const completed = ref(false)

const question = computed(() => questions.value[currentStep.value])
const isFirst = computed(() => currentStep.value === 0)
const isLast = computed(() => currentStep.value === questions.value.length - 1)
const progressPct = computed(() => Math.round(((currentStep.value + 1) / questions.value.length) * 100))

function select(value) {
  answers.value[question.value.id] = value

  if (question.value.id === 'language') {
    locale.value = value
    localStorage.setItem('profileLanguage', value)
    emit('languageChange', value)
  }

  if (!isLast.value) {
    slideDirection.value = 'next'
    currentStep.value++
  } else {
    completed.value = true
    emit('complete', answers.value)
  }
}

function back() {
  if (!isFirst.value) {
    slideDirection.value = 'prev'
    currentStep.value--
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-50 to-violet-100 p-6">
    <div class="bg-white rounded-2xl p-10 w-full max-w-md min-h-96 shadow-lg flex flex-col">

      <template v-if="!completed">
        <!-- Progress -->
        <div class="h-1 bg-violet-100 rounded-full overflow-hidden mb-2">
          <div
            class="h-full bg-indigo-600 rounded-full transition-all duration-300"
            :style="{ width: progressPct + '%' }"
          />
        </div>
        <p class="text-xs font-semibold tracking-wider uppercase text-violet-500 mb-8">
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
          <div :key="currentStep" class="flex-1">
            <h2 class="text-2xl font-bold text-indigo-950 leading-snug mb-2">{{ question.label }}</h2>
            <p class="text-sm text-gray-500 leading-relaxed mb-8">{{ question.sublabel }}</p>

            <!-- Choice -->
            <div v-if="question.type === 'choice'" class="grid grid-cols-2 gap-3">
              <button
                v-for="opt in question.options"
                :key="opt.value"
                class="py-3.5 px-4 border-2 rounded-xl text-sm font-medium cursor-pointer transition-all duration-150"
                :class="answers[question.id] === opt.value
                  ? 'border-indigo-600 bg-indigo-600 text-white'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-300 hover:bg-violet-50 hover:text-indigo-600'"
                @click="select(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>

            <!-- Boolean -->
            <div v-else-if="question.type === 'boolean'" class="grid grid-cols-2 gap-4">
              <button
                class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                :class="answers[question.id] === true
                  ? 'border-indigo-600 bg-indigo-600 text-white'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-600 hover:bg-indigo-600 hover:text-white'"
                @click="select(true)"
              >
                {{ t('profile.yes') }}
              </button>
              <button
                class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                :class="answers[question.id] === false
                  ? 'border-indigo-600 bg-indigo-600 text-white'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-600 hover:bg-indigo-600 hover:text-white'"
                @click="select(false)"
              >
                {{ t('profile.no') }}
              </button>
            </div>
          </div>
        </Transition>

        <button
          v-if="!isFirst"
          class="mt-6 self-start text-sm font-medium text-violet-500 hover:text-indigo-600 transition-colors duration-150 cursor-pointer bg-transparent border-none p-0"
          @click="back"
        >
          <ArrowLeftIcon class="w-4 h-4 inline" /> {{ t('profile.back') }}
        </button>
      </template>

      <!-- Done -->
      <template v-else>
        <div class="flex-1 flex flex-col items-center justify-center text-center gap-3">
          <div class="w-16 h-16 bg-indigo-600 text-white rounded-full flex items-center justify-center mb-2">
            <CheckIcon class="w-8 h-8" />
          </div>
          <h2 class="text-2xl font-bold text-indigo-950">{{ t('profile.done.title') }}</h2>
          <p class="text-sm text-gray-500">{{ t('profile.done.subtitle') }}</p>
        </div>
      </template>

    </div>
  </div>
</template>
