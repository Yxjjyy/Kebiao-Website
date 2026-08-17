import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/pages/DashboardPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
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

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (auth.authenticated === null) {
    await auth.verify()
  }
  if (to.path === '/login') {
    return auth.isAuthenticated ? '/' : true
  }
  return auth.isAuthenticated ? true : '/login'
})

export default router
