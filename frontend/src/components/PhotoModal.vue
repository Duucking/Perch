<template>
  <transition name="modal-enter">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal-container">
        <div class="modal-topbar">
          <div class="modal-info">
            <span class="modal-filename">{{ photo?.filename }}</span>
          </div>
          <div class="modal-actions">
            <a v-if="photo" class="btn-icon" :href="`/api/download/${photo.id}`" download title="下载">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </a>
            <button class="btn-icon" @click="close" title="关闭">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="modal-body">
          <div class="modal-image-wrap" @click="toggleZoom">
            <div class="modal-image" :class="{ zoomed }" v-if="photo">
              <img :src="`/api/photo-file/${photo.id}`" :alt="photo.filename" @load="imgLoaded = true" />
            </div>
            <div v-if="!imgLoaded" class="modal-skeleton"></div>
          </div>

          <div v-if="exif" class="modal-exif">
            <div class="exif-row" v-if="exif.aperture">
              <span class="exif-label">光圈</span>
              <span class="exif-value">{{ exif.aperture }}</span>
            </div>
            <div class="exif-row" v-if="exif.shutter">
              <span class="exif-label">快门</span>
              <span class="exif-value">{{ exif.shutter }}</span>
            </div>
            <div class="exif-row" v-if="exif.iso">
              <span class="exif-label">ISO</span>
              <span class="exif-value">{{ exif.iso }}</span>
            </div>
            <div class="exif-row" v-if="exif.datetime">
              <span class="exif-label">拍摄时间</span>
              <span class="exif-value">{{ exif.datetime }}</span>
            </div>
            <div class="exif-row" v-if="photo">
              <span class="exif-label">尺寸</span>
              <span class="exif-value">{{ photo.width }} × {{ photo.height }}</span>
            </div>
          </div>

          <div v-else-if="exifLoaded && !exif" class="no-exif">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>无拍摄参数信息</span>
          </div>

          <div v-if="photo?.description" class="modal-story">
            <div class="story-body">{{ photo.description }}</div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: Boolean,
  photoId: Number
})
const emit = defineEmits(['close'])

const photo = ref(null)
const exif = ref(null)
const exifLoaded = ref(false)
const imgLoaded = ref(false)
const zoomed = ref(false)

watch(() => props.photoId, async (id) => {
  if (!id) return
  imgLoaded.value = false
  zoomed.value = false
  try {
    const res = await fetch(`/api/photos/${id}`)
    const data = await res.json()
    photo.value = data
    exif.value = data.exif || null
    exifLoaded.value = true
  } catch {
    photo.value = null
    exifLoaded.value = true
  }
})

watch(() => props.visible, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})

onUnmounted(() => {
  document.body.style.overflow = ''
})

function close() {
  photo.value = null
  exif.value = null
  exifLoaded.value = false
  imgLoaded.value = false
  zoomed.value = false
  emit('close')
}

function toggleZoom() {
  zoomed.value = !zoomed.value
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: var(--bg-overlay);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal-container {
  width: 100%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  animation: modal-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.modal-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-filename {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 400;
}

.modal-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-icon:hover {
  background: var(--accent);
  color: var(--bg-primary);
  border-color: var(--accent);
  transform: translateY(-1px);
}

.modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-image-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-in;
  overflow: hidden;
  min-height: 400px;
  background: var(--bg-secondary);
  position: relative;
}

.modal-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-image.zoomed {
  cursor: zoom-out;
}

.modal-image.zoomed img {
  transform: scale(2);
  cursor: zoom-out;
}

.modal-image img {
  max-width: 100%;
  max-height: 65vh;
  object-fit: contain;
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  animation: img-fade-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.modal-skeleton {
  position: absolute;
  inset: 0;
  background: var(--bg-secondary);
}

.modal-skeleton::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.modal-exif {
  display: flex;
  gap: 0;
  border-top: 1px solid var(--border);
  background: var(--bg-primary);
}

.exif-row {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  border-right: 1px solid var(--border);
  text-align: center;
}

.exif-row:last-child {
  border-right: none;
}

.exif-label {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 4px;
  font-weight: 500;
}

.exif-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 400;
  font-family: 'Inter', monospace;
}

.no-exif {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 13px;
}

@keyframes modal-in {
  from { opacity: 0; transform: scale(0.92) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes img-fade-in {
  from { opacity: 0; filter: blur(8px); }
  to { opacity: 1; filter: blur(0); }
}

.modal-enter-enter-active {
  transition: all 0.3s;
}
.modal-enter-enter-from {
  opacity: 0;
}
.modal-enter-leave-active {
  transition: all 0.2s;
}
.modal-enter-leave-to {
  opacity: 0;
}

.modal-story {
  border-top: 1px solid var(--border);
  padding: 20px 28px;
  background: var(--bg-primary);
}

.story-body {
  font-family: 'Noto Serif SC', 'SimSun', '宋体', serif;
  font-size: 14px;
  line-height: 1.9;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  text-indent: 2em;
  position: relative;
  padding-left: 4px;
}

.story-body::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
  border-radius: 2px;
  opacity: 0.4;
}
</style>