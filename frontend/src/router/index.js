import { createRouter, createWebHistory } from 'vue-router'
import ProfileSetupView from '@/views/ProfileSetupView.vue'
import CategoryDetailView from '@/views/CategoryDetailView.vue'
import AdminResourceListView from '@/views/AdminResourceListView.vue'
import AdminResourceFormView from '@/views/AdminResourceFormView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ProfileSetupView },
    { path: '/categories/:id?', component: CategoryDetailView },
    { path: '/admin/resources', component: AdminResourceListView },
    { path: '/admin/resources/new', component: AdminResourceFormView },
    { path: '/admin/resources/:id/edit', component: AdminResourceFormView },
  ],
})

export default router
