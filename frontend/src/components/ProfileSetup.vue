<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  initialAnswers: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['complete'])

const questions = [
  {
    id: 'language',
    type: 'choice',
    label: 'What is your preferred language?',
    sublabel: 'Resources will be displayed in the language you choose.',
    options: [
      { value: 'en', label: 'English' },
      { value: 'fr', label: 'Français' },
      { value: 'es', label: 'Español' },
      { value: 'ar', label: 'العربية' },
      { value: 'pt', label: 'Português' },
      { value: 'zh', label: '中文' },
    ],
  },
  {
    id: 'status',
    type: 'choice',
    label: 'What is your permit type?',
    sublabel: 'This is your Swiss residence permit. It is the card you got when you arrived.',
    options: [
      { value: 'N', label: 'Permit N' },
      { value: 'F', label: 'Permit F' },
      { value: 'S', label: 'Permit S' },
      { value: 'B', label: 'Permit B' },
      { value: 'C', label: 'Permit C' },
      { value: 'L', label: 'Permit L' },
      { value: 'G', label: 'Permit G' },
      { value: 'other', label: 'I do not know' },
    ],
  },
  {
    id: 'hasChildren',
    type: 'boolean',
    label: 'Do you have children?',
    sublabel: 'This helps us recommend the right family resources.',
  },
]

const currentStep = ref(0)
const slideDirection = ref('next')
const answers = ref({ ...props.initialAnswers })
const completed = ref(false)

const question = computed(() => questions[currentStep.value])
const isFirst = computed(() => currentStep.value === 0)
const isLast = computed(() => currentStep.value === questions.length - 1)
const progressPct = computed(() => Math.round(((currentStep.value + 1) / questions.length) * 100))

function select(value) {
  answers.value[question.value.id] = value
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
          Step {{ currentStep + 1 }} of {{ questions.length }}
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
                Yes
              </button>
              <button
                class="py-5 border-2 rounded-2xl text-base font-semibold cursor-pointer transition-all duration-150"
                :class="answers[question.id] === false
                  ? 'border-indigo-600 bg-indigo-600 text-white'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-600 hover:bg-indigo-600 hover:text-white'"
                @click="select(false)"
              >
                No
              </button>
            </div>
          </div>
        </Transition>

        <button
          v-if="!isFirst"
          class="mt-6 self-start text-sm font-medium text-violet-500 hover:text-indigo-600 transition-colors duration-150 cursor-pointer bg-transparent border-none p-0"
          @click="back"
        >
          ← Back
        </button>
      </template>

      <!-- Done -->
      <template v-else>
        <div class="flex-1 flex flex-col items-center justify-center text-center gap-3">
          <div class="w-16 h-16 bg-indigo-600 text-white rounded-full flex items-center justify-center text-2xl mb-2">
            ✓
          </div>
          <h2 class="text-2xl font-bold text-indigo-950">You're all set!</h2>
          <p class="text-sm text-gray-500">We're preparing your personalized resources.</p>
        </div>
      </template>

    </div>
  </div>
</template>

