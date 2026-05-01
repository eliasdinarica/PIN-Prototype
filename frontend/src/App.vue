<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from '@/components/AppNav.vue'

const route = useRoute()
const showNav = computed(() => route.path !== '/')
</script>

<template>
  <AppNav v-if="showNav" />
  <RouterView />
</template>
