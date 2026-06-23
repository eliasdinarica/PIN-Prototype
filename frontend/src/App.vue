<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import TopBar from '@/components/TopBar.vue'

const route = useRoute()
const showNav = computed(() => route.path !== '/' && route.path !== '/profile')
</script>

<template>
  <TopBar v-if="showNav" />
  <AppNav v-if="showNav" />
  <RouterView />
</template>
