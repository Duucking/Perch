import { createRouter, createWebHistory } from 'vue-router'
import Gallery from '../views/Gallery.vue'
import PhotoDetail from '../views/PhotoDetail.vue'

const routes = [
  { path: '/', name: 'gallery', component: Gallery },
  { path: '/photo/:id', name: 'photo-detail', component: PhotoDetail, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router