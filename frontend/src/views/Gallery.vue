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
      <p>请联系管理员扫描目录添加照片</p>
    </div>

    <div v-else ref="masonryRef" class="photo-masonry" :style="{ position: 'relative', width: '100%', height: masonryHeight }">
      <div
        v-for="(item, index) in positionedItems"
        :key="item.photo.id"
        class="masonry-item"
        :style="item.style"
        @click="openModal(item.photo.id)"
      >
        <div class="masonry-card">
          <div class="masonry-img-wrap" :style="imgWrapStyle(item.photo)">
            <img
              :src="getThumbUrl(item.photo.thumbnail_path)"
              :alt="item.photo.filename"
              class="masonry-img"
              referrerpolicy="no-referrer"
              @load="onImgLoad($event)"
              @error="onImgLoad($event)"
            />
            <div class="img-skeleton"></div>
          </div>
          <div class="card-overlay">
            <div class="card-info">
              <span class="card-name">{{ item.photo.filename }}</span>
              <span class="card-dimensions">{{ item.photo.width }} × {{ item.photo.height }}</span>
            </div>
          </div>
        </div>
      </div>

      </div>

    <PhotoModal :visible="modalVisible" :photo-id="modalPhotoId" @close="closeModal" />

    <div ref="sentinel" class="sentinel"></div>

    <div v-if="store.loadingMore" class="loading-mask">
      <div class="loading-mask-inner">
        <div class="loading-spinner"></div>
        <p>正在加载...</p>
      </div>
    </div>

    <div v-if="store.allLoaded && store.photos.length" class="end-message">
      — 已显示全部 {{ store.total }} 张照片 —
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useGalleryStore } from '../stores/gallery'
import PhotoModal from '../components/PhotoModal.vue'

const store = useGalleryStore()
const searchInput = ref('')
const sentinel = ref(null)
const masonryRef = ref(null)
const windowWidth = ref(window.innerWidth)
const colWidth = ref(260)
const modalVisible = ref(false)
const modalPhotoId = ref(0)
const containerWidth = ref(0)
const gap = 20
let searchTimer = null
let resizeTimer = null
let layoutTimer = null
let scrollTimer = null

const columnCount = computed(() => {
  const w = windowWidth.value
  if (w > 1200) return 4
  if (w > 900) return 3
  if (w > 480) return 2
  return 1
})

function calcColWidth() {
  if (!masonryRef.value) return
  const rect = masonryRef.value.getBoundingClientRect()
  containerWidth.value = rect.width
  const cols = columnCount.value
  colWidth.value = (rect.width - gap * (cols - 1)) / cols
}

const positionedItems = computed(() => {
  const cols = columnCount.value
  const w = colWidth.value
  const heights = new Array(cols).fill(0)

  return store.photos.map((photo, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    const aspect = photo.width / photo.height || 1
    const cardH = w / aspect
    const top = heights[col]
    heights[col] += cardH + gap

    return {
      photo,
      style: {
        position: 'absolute',
        width: `${w}px`,
        left: `${col * (w + gap)}px`,
        top: `${top}px`,
        '--delay': `${row * 0.06}s`
      }
    }
  })
})

const masonryHeight = computed(() => {
  if (!positionedItems.value.length) return '0px'
  const cols = columnCount.value
  const w = colWidth.value
  const heights = new Array(cols).fill(0)
  for (const item of positionedItems.value) {
    const col = store.photos.indexOf(item.photo) % cols
    const aspect = item.photo.width / item.photo.height || 1
    heights[col] += w / aspect + gap
  }
  return `${Math.max(...heights)}px`
})

function layout() {
  if (!masonryRef.value) return
  calcColWidth()

  const cols = columnCount.value
  const w = colWidth.value
  const heights = new Array(cols).fill(0)
  const cards = masonryRef.value.querySelectorAll('.masonry-item')

  cards.forEach((el, i) => {
    const col = i % cols
    el.style.width = `${w}px`
    el.style.left = `${col * (w + gap)}px`
    el.style.top = `${heights[col]}px`
    heights[col] += el.offsetHeight + gap
  })

  masonryRef.value.style.height = `${Math.max(...heights, 0)}px`
}

watch([() => store.photos.length, () => store.loadingMore], async () => {
  await nextTick()
  layout()
  await nextTick()
  if (store.loadingMore || store.allLoaded) return
  if (!sentinel.value) return
  const rect = sentinel.value.getBoundingClientRect()
  const wp = window.innerHeight + 300
  if (rect.top < wp) {
    store.loadMore()
  }
})

watch(columnCount, async (n) => {
  store.setCols(n)
  await nextTick()
  layout()
})

function checkLoadMore() {
  if (store.loadingMore || store.allLoaded) return
  if (!sentinel.value) return
  const rect = sentinel.value.getBoundingClientRect()
  if (rect.top < window.innerHeight + 400) {
    store.loadMore()
  }
}

onMounted(async () => {
  store.setCols(columnCount.value)
  store.fetchPhotos()
  await nextTick()

  window.addEventListener('scroll', onScroll)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResize)
  clearTimeout(resizeTimer)
  clearTimeout(scrollTimer)
})

function onScroll() {
  clearTimeout(scrollTimer)
  scrollTimer = setTimeout(checkLoadMore, 100)
}

function onResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    windowWidth.value = window.innerWidth
    nextTick(() => layout())
  }, 150)
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    store.setSearch(searchInput.value)
  }, 400)
}

function imgWrapStyle(photo) {
  const w = colWidth.value || 260
  const h = w / (photo.width / photo.height || 1)
  return { height: `${h}px` }
}

function getThumbUrl(path) {
  if (!path) return ''
  const parts = path.replace(/\\/g, '/').split('/')
  const filename = parts[parts.length - 1]
  return `/api/thumbnails/${filename}`
}

function onImgLoad(e) {
  if (!layoutTimer) {
    layoutTimer = setTimeout(() => {
      layout()
      layoutTimer = null
    }, 80)
  }
}

function openModal(id) {
  modalPhotoId.value = id
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  modalPhotoId.value = 0
}
</script>

<style scoped>
.gallery {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 32px 80px;
}

@media (max-width: 600px) {
  .gallery {
    padding: 24px 16px 80px;
  }
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

@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .gallery-title {
    font-size: 24px;
  }
  .search-box {
    max-width: 100%;
    width: 100%;
  }
  .search-box input {
    width: 100%;
  }
  .search-box input:focus {
    width: 100%;
  }
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

.search-box {
  max-width: 60vw;
}

.search-box input {
  width: 200px;
  max-width: 100%;
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
  width: 260px;
  max-width: 100%;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--shadow);
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.photo-masonry {
  position: relative;
  width: 100%;
}

.masonry-item {
  position: absolute;
  cursor: pointer;
  animation: card-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: var(--delay);
  will-change: transform, opacity;
}

.masonry-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.masonry-card:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: 0 16px 48px var(--shadow-strong);
  border-color: var(--accent);
}

.masonry-img-wrap {
  position: relative;
  overflow: hidden;
  background: var(--bg-secondary);
}

.masonry-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: relative;
  z-index: 1;
  transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.masonry-img.loaded ~ .img-skeleton {
  opacity: 0;
  pointer-events: none;
}

.img-skeleton {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: var(--bg-secondary);
  overflow: hidden;
  transition: opacity 0.4s;
}

.img-skeleton::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.masonry-card:hover .masonry-img {
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

.masonry-card:hover .card-overlay {
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

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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

.sentinel {
  height: 1px;
}

.loading-mask {
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: mask-fade-in 0.4s ease;
  margin-top: -1px;
}

.loading-mask-inner {
  text-align: center;
}

.loading-mask-inner .loading-spinner {
  width: 28px;
  height: 28px;
  border-width: 2px;
  margin: 0 auto 12px;
}

.loading-mask-inner p {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 300;
  letter-spacing: 2px;
}

@keyframes mask-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.end-message {
  text-align: center;
  padding: 48px 32px;
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 300;
  letter-spacing: 1px;
}
</style>