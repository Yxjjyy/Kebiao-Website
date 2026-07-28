import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/pages/DashboardPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      redirect: '/',
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardPage,
    },
    {
      path: '/students',
      name: 'students',
      component: DashboardPage,
    },
    {
      path: '/stats',
      name: 'stats',
      component: DashboardPage,
    },
    {
      path: '/settings',
      name: 'settings',
      component: DashboardPage,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

export default router
