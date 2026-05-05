<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import CategoryCard from '@/components/CategoryCard.vue'

const router = useRouter()
const { t } = useI18n()
const categories = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/api/categories/')
    categories.value = await res.json()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-surface-100 to-surface-200">

    <div class="max-w-5xl mx-auto px-5 py-12">

      <!-- Header -->
      <p class="text-xs font-semibold tracking-wider uppercase text-surface-500 mb-2">{{ t('categories.eyebrow') }}</p>
      <h1 class="text-3xl font-bold text-surface-950 mb-10">{{ t('categories.title') }}</h1>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-surface-200 border-t-surface-600 rounded-full animate-spin" />
      </div>

      <!-- Empty -->
      <div v-else-if="categories.length === 0" class="bg-white rounded-2xl p-12 text-center text-gray-400 shadow-sm">
        {{ t('categories.empty') }}
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <CategoryCard
          v-for="cat in categories"
          :key="cat.id"
          :category="cat"
          @click="router.push(`/categories/${cat.id}`)"
        />
      </div>

    </div>
  </div>
</template>
