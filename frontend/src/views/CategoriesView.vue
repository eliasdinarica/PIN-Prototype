<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CategoryCard from '@/components/CategoryCard.vue'

const router = useRouter()
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
  <div class="min-h-screen bg-gradient-to-br from-violet-50 to-violet-100">

    <div class="max-w-5xl mx-auto px-5 py-12">

      <!-- Header -->
      <p class="text-xs font-semibold tracking-wider uppercase text-violet-500 mb-2">Your resources</p>
      <h1 class="text-3xl font-bold text-indigo-950 mb-10">What do you need help with?</h1>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      </div>

      <!-- Empty -->
      <div v-else-if="categories.length === 0" class="bg-white rounded-2xl p-12 text-center text-gray-400 shadow-sm">
        No categories yet.
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
