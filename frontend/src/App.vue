<template>
  <div class="app" :class="{ 'dark-mode': store.darkMode }">
    <nav class="nav" v-if="!isAdminRoute">
      <div class="nav-inner">
        <router-link to="/" class="nav-brand" @click="navigateHome">
          <span class="brand-icon">栖</span>
          <span class="brand-text">Perch</span>
        </router-link>
        <div class="nav-actions">
          <span class="photo-count" v-if="store.total > 0">
            {{ store.total }} 张照片
          </span>
          <button class="btn-theme" @click="store.toggleDarkMode()" :title="store.darkMode ? '切换亮色模式' : '切换深色模式'">
            <svg v-if="store.darkMode" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <main class="main-content" :class="{ 'no-nav': isAdminRoute }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <footer class="footer" v-if="!isAdminRoute">
      <p>栖所 Perch &mdash; 光影之间，片刻永恒</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGalleryStore } from './stores/gallery'
import { useAuthStore } from './stores/auth'

const store = useGalleryStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const isAdminRoute = computed(() => route.path.startsWith('/admin'))

onMounted(async () => {
  store.applyTheme()
  store.fetchStats()
  await auth.restore()
})

function navigateHome() {
  router.push('/')
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--nav-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  transition: background 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-primary);
  cursor: pointer;
}

.brand-icon {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  color: var(--accent);
  font-weight: 700;
}

.brand-text {
  font-family: 'Inter', sans-serif;
  font-size: 18px;
  font-weight: 300;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.photo-count {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 300;
  letter-spacing: 0.5px;
}

.btn-theme {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-theme:hover {
  background: var(--accent);
  color: var(--bg-primary);
  border-color: var(--accent);
  transform: rotate(15deg);
}

.main-content {
  flex: 1;
  padding-top: 64px;
}

.main-content.no-nav {
  padding-top: 0;
}

.footer {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 300;
  letter-spacing: 1px;
  border-top: 1px solid var(--border);
}
</style>