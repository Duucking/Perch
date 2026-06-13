<template>
  <div class="gallery">
    <header class="gallery-header">
      <div class="header-content">
        <h1 class="gallery-title" v-if="!store.searchQuery">
          光影集
          <span class="title-sub">Gallery of Light</span>
        </h1>
        <div class="search-box">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            v-model="searchInput"
            type="text"
            placeholder="搜索照片..."
            @input="onSearchInput"
          />
        </div>
      </div>
    </header>

    <div v-if="store.loading && !store.photos.length" class="loading-state">
      <div class="loading-spinner"></div>
      <p>正在加载光影...</p>
    </div>

    <div v-else-if="!store.photos.length && !store.loading" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>
        </svg>
      </div>
      <h2>还没有照片</h2>
      <p>点击右上角的 <strong>+</strong> 按钮扫描目录添加照片</p>
    </div>

    <transition-group
      v-else
      name="scale-in"
      tag="div"
      class="photo-grid"
      appear
    >
      <div
        v-for="(photo, index) in store.photos"
        :key="photo.id"
        class="photo-card"
        :style="{ '--delay': `${index * 0.05}s` }"
        @click="openDetail(photo.id)"
      >
        <div class="card-image-wrapper">
          <div
            class="card-image"
            :style="{
              backgroundImage: `url(${getThumbUrl(photo.thumbnail_path)})`,
              aspectRatio: photo.width / photo.height
            }"
          >
            <div class="card-overlay">
              <div class="card-info">
                <span class="card-name">{{ photo.filename }}</span>
                <span class="card-dimensions">{{ photo.width }} × {{ photo.height }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition-group>

    <div v-if="store.totalPages > 1" class="pagination">
      <button
        :disabled="store.page <= 1"
        @click="store.setPage(store.page - 1)"
        class="page-btn"
      >
        ← 上一页
      </button>
      <span class="page-info">{{ store.page }} / {{ store.totalPages }}</span>
      <button
        :disabled="store.page >= store.totalPages"
        @click="store.setPage(store.page + 1)"
        class="page-btn"
      >
        下一页 →
      </button>
    </div>

    <div v-if="store.loading && store.photos.length" class="loading-more">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGalleryStore } from '../stores/gallery'

const store = useGalleryStore()
const router = useRouter()
const searchInput = ref('')
let searchTimer = null

onMounted(() => {
  store.fetchPhotos()
})

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    store.setSearch(searchInput.value)
  }, 400)
}

function getThumbUrl(path) {
  if (!path) return ''
  const parts = path.replace(/\\/g, '/').split('/')
  const filename = parts[parts.length - 1]
  return `/api/thumbnails/${filename}`
}

function openDetail(id) {
  router.push({ name: 'photo-detail', params: { id } })
}
</script>

<style scoped>
.gallery {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 32px 80px;
}

.gallery-header {
  margin-bottom: 48px;
}

.header-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.gallery-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.title-sub {
  display: block;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 300;
  color: var(--text-muted);
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-top: 4px;
}

.search-box {
  position: relative;
  flex-shrink: 0;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-box input {
  width: 240px;
  padding: 10px 14px 10px 40px;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-box input:focus {
  width: 300px;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--shadow);
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.photo-card {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  animation-delay: var(--delay);
}

.photo-card:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: 0 16px 48px var(--shadow-strong);
  border-color: var(--accent);
}

.card-image-wrapper {
  position: relative;
  overflow: hidden;
}

.card-image {
  width: 100%;
  background-size: cover;
  background-position: center;
  transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.photo-card:hover .card-image {
  transform: scale(1.08);
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.6) 0%,
    transparent 50%
  );
  opacity: 0;
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: flex-end;
}

.photo-card:hover .card-overlay {
  opacity: 1;
}

.card-info {
  padding: 16px;
  width: 100%;
}

.card-name {
  display: block;
  color: #fff;
  font-size: 13px;
  font-weight: 400;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-dimensions {
  display: block;
  color: rgba(255,255,255,0.7);
  font-size: 11px;
  margin-top: 2px;
  font-weight: 300;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 32px;
  text-align: center;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.empty-state p {
  color: var(--text-muted);
  font-size: 14px;
  margin-top: 8px;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 48px;
}

.page-btn {
  padding: 10px 20px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 300;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: 32px;
}
</style>