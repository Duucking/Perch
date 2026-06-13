import { createRouter, createWebHistory } from 'vue-router'
import Gallery from '../views/Gallery.vue'
import AdminLogin from '../views/AdminLogin.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

const routes = [
  { path: '/', name: 'gallery', component: Gallery },
  { path: '/admin', name: 'admin-login', component: AdminLogin },
  { path: '/admin/dashboard', name: 'admin-dashboard', component: AdminDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router