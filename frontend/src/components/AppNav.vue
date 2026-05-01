<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="fixed top-4 right-4 z-50">
    <button
      class="flex items-center gap-2 bg-white shadow-md rounded-full pl-3 pr-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 border border-indigo-100 transition-all duration-150 cursor-pointer"
      @click="router.push('/')"
    >
      <span class="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs">👤</span>
      <span>Edit profile</span>
    </button>
  </div>
</template>
