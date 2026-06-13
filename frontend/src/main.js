import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/main.css'

const origFetch = window.fetch.bind(window)
window.fetch = (url, opts = {}) => {
  const headers = new Headers(opts.headers || {})
  if (!headers.has('X-Requested-With')) {
    headers.set('X-Requested-With', 'XMLHttpRequest')
  }
  return origFetch(url, { ...opts, headers })
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')