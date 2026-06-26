<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  BuildingOffice2Icon, MapPinIcon, PhoneIcon, EnvelopeIcon,
  DocumentDuplicateIcon, CheckIcon,
} from '@heroicons/vue/24/outline'
import ResourceMap from '@/components/ResourceMap.vue'

const { t } = useI18n()

const props = defineProps({
  places: { type: Array, default: () => [] },
  // Content language, so the heading matches the body shown (not the UI locale).
  lang: { type: String, default: 'fr' },
})

const copiedKey = ref(null)
async function copy(value, key) {
  try {
    await navigator.clipboard.writeText(value)
    copiedKey.value = key
    setTimeout(() => { if (copiedKey.value === key) copiedKey.value = null }, 1500)
  } catch { /* clipboard unavailable */ }
}

function rows(place, i) {
  const r = []
  if (place.address) r.push({ key: `a${i}`, icon: MapPinIcon, value: place.address })
  if (place.phone) r.push({ key: `p${i}`, icon: PhoneIcon, value: place.phone })
  if (place.email) r.push({ key: `e${i}`, icon: EnvelopeIcon, value: place.email })
  return r
}

const hasMap = () => props.places.some(p => p.lat != null && p.lng != null)
</script>

<template>
  <div class="bg-white rounded-2xl shadow-sm border border-surface-100 p-6">
    <h2 class="text-2xl font-bold text-surface-800 leading-tight mb-4">{{ t('article.location', {}, { locale: lang }) }}</h2>

    <div class="grid gap-4" :class="hasMap() ? 'lg:grid-cols-2' : ''">

      <!-- Left: structured place cards -->
      <div class="space-y-3">
        <div
          v-for="(place, i) in places"
          :key="i"
          class="rounded-xl border border-surface-200 overflow-hidden"
        >
          <div class="bg-brand-50 px-4 py-3">
            <p class="font-bold text-brand-700 leading-snug">{{ place.name }}</p>
            <p v-if="place.city" class="flex items-center gap-1.5 text-sm text-surface-500 mt-0.5">
              <BuildingOffice2Icon class="w-4 h-4 shrink-0" />{{ place.city }}
            </p>
          </div>
          <div v-if="rows(place, i).length" class="divide-y divide-surface-100">
            <div
              v-for="row in rows(place, i)"
              :key="row.key"
              class="flex items-center gap-3 px-4 py-2.5"
            >
              <component :is="row.icon" class="w-4 h-4 text-surface-400 shrink-0" />
              <span class="flex-1 min-w-0 text-sm text-surface-700 break-words">{{ row.value }}</span>
              <button
                class="w-7 h-7 flex items-center justify-center rounded-lg text-surface-400 hover:text-brand-600 hover:bg-surface-100 transition-colors cursor-pointer bg-transparent border-none shrink-0"
                :aria-label="t('actions.copy')"
                @click="copy(row.value, row.key)"
              >
                <CheckIcon v-if="copiedKey === row.key" class="w-4 h-4 text-green-500" />
                <DocumentDuplicateIcon v-else class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: map -->
      <ResourceMap v-if="hasMap()" :places="places" />
    </div>
  </div>
</template>
