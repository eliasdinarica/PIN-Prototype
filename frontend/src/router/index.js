import { createRouter, createWebHistory } from 'vue-router'
import ProfileSetupView from '@/views/ProfileSetupView.vue'
import CategoryDetailView from '@/views/CategoryDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ProfileSetupView },
    { path: '/categories/:id?', component: CategoryDetailView },
  ],
})

export default router
