import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import HubView from '@/views/HubView.vue'
import ProfileSetupView from '@/views/ProfileSetupView.vue'
import CategoryDetailView from '@/views/CategoryDetailView.vue'
import AdminResourceListView from '@/views/AdminResourceListView.vue'
import AdminResourceFormView from '@/views/AdminResourceFormView.vue'
import PathwaysView from '@/views/PathwaysView.vue'
import PathwayDetailView from '@/views/PathwayDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LandingView },
    { path: '/hub', component: HubView },
    { path: '/profile', component: ProfileSetupView },
    { path: '/categories/:id?', component: CategoryDetailView },
    { path: '/pathways', component: PathwaysView },
    { path: '/pathways/:id', component: PathwayDetailView },
    { path: '/admin/resources', component: AdminResourceListView },
    { path: '/admin/resources/new', component: AdminResourceFormView },
    { path: '/admin/resources/:id/edit', component: AdminResourceFormView },
  ],
})

export default router
