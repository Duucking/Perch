<template>
  <div class="photo-detail" v-if="photo">
    <div class="detail-backdrop" @click="goBack"></div>

    <div class="detail-container">
      <div class="detail-topbar">
        <button class="btn-back" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          <span>返回</span>
        </button>
        <div class="topbar-info">
          <span class="detail-filename">{{ photo.filename }}</span>
          <span class="detail-dims">{{ photo.width }} × {{ photo.height }}</span>
        </div>
        <div class="topbar-actions">
          <button class="btn-action" @click="toggleZoom" :title="zoomed ? '缩小' : '放大'">
            <svg v-if="!zoomed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/><path d="M11 8v6"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/>
            </svg>
          </button>
          <a class="btn-action" :href="`/api/download/${photo.id}`" download :title="'下载照片'">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </a>
        </div>
      </div>

      <div
        class="detail-image-wrapper"
        :class="{ zoomed }"
        @click="toggleZoom"
      >
        <div
          class="detail-image"
          :style="{
            backgroundImage: `url(${photoUrl})`,
            animationDelay: '0.2s'
          }"
        ></div>
      </div>

      <div class="detail-footer">
        <div class="footer-meta">
          <span>{{ formatSize(photo.file_size) }}</span>
          <span class="meta-sep">·</span>
          <span>{{ photo.scanned_at }}</span>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="detail-loading">
    <div class="loading-spinner"></div>
    <p>正在加载...</p>
  </div>

  <div v-else class="detail-error">
    <p>照片未找到</p>
    <button class="btn-back" @click="goBack">返回画廊</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const photo = ref(null)
const loading = ref(true)
const zoomed = ref(false)

let photoUrl = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`/api/photos/${route.params.id}`)
    if (!res.ok) throw new Error('Not found')
    photo.value = await res.json()
    photoUrl.value = `/api/photo-file/${photo.value.id}`
  } catch (e) {
    photo.value = null
  } finally {
    loading.value = false
  }

  document.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown)
})

function onKeyDown(e) {
  if (e.key === 'Escape') goBack()
  if (e.key === 'z' || e.key === 'Z') toggleZoom()
}

function goBack() {
  router.back()
}

function toggleZoom() {
  zoomed.value = !zoomed.value
}

function formatSize(bytes) {
  if (!bytes) return '未知'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}
</script>

<style scoped>
.photo-detail {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: blur-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.detail-backdrop {
  position: absolute;
  inset: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(8px);
}

.detail-container {
  position: relative;
  z-index: 1;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: scale-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s;
}

.btn-back:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.topbar-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-filename {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 400;
}

.detail-dims {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 300;
}

.topbar-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-action:hover {
  background: var(--accent);
  color: var(--bg-primary);
  border-color: var(--accent);
  transform: translateY(-2px);
}

.detail-image-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-in;
  overflow: hidden;
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  min-height: 60vh;
}

.detail-image-wrapper.zoomed {
  cursor: zoom-out;
}

.detail-image-wrapper.zoomed .detail-image {
  transform: scale(1.8);
  cursor: zoom-out;
}

.detail-image {
  width: 100%;
  height: 70vh;
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  animation: blur-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.detail-footer {
  padding: 12px 0;
  text-align: center;
}

.footer-meta {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 300;
}

.meta-sep {
  margin: 0 8px;
}

.detail-loading,
.detail-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 16px;
  color: var(--text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes blur-in {
  from {
    opacity: 0;
    filter: blur(20px);
    transform: scale(1.05);
  }
  to {
    opacity: 1;
    filter: blur(0);
    transform: scale(1);
  }
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.92);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>