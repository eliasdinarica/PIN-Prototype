<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import ChatAssistant from '@/components/ChatAssistant.vue'

const route = useRoute()
const showNav = computed(() => route.path !== '/' && route.path !== '/profile')
</script>

<template>
  <AppNav v-if="showNav" />
  <RouterView />
  <ChatAssistant v-if="showNav" />
</template>
