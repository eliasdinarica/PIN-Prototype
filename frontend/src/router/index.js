import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import HubView from '@/views/HubView.vue'
import ProfileSetupView from '@/views/ProfileSetupView.vue'
import SearchView from '@/views/SearchView.vue'
import AdminResourceListView from '@/views/AdminResourceListView.vue'
import AdminResourceFormView from '@/views/AdminResourceFormView.vue'
import ResourceShareView from '@/views/ResourceShareView.vue'
import GuideShareView from '@/views/GuideShareView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LandingView },
    { path: '/hub', component: HubView },
    { path: '/profile', component: ProfileSetupView },
    { path: '/categories', component: SearchView },
    { path: '/search', component: SearchView },
    { path: '/r/:id', component: ResourceShareView },
    { path: '/g/:id', component: GuideShareView },
    { path: '/admin/resources', component: AdminResourceListView },
    { path: '/admin/resources/new', component: AdminResourceFormView },
    { path: '/admin/resources/:id/edit', component: AdminResourceFormView },
  ],
})

export default router
