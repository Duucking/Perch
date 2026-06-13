<template>
  <transition name="slide-up">
    <div class="scan-panel">
      <div class="scan-inner">
        <div class="scan-header">
          <h3>扫描目录</h3>
          <button class="btn-close" @click="$emit('close')">&times;</button>
        </div>
        <div class="scan-body">
          <div class="dir-browser">
            <div class="dir-input">
              <input
                v-model="currentPath"
                type="text"
                placeholder="输入目录路径或浏览..."
                @keyup.enter="browseDir(currentPath)"
              />
              <button class="btn-go" @click="browseDir(currentPath)">浏览</button>
            </div>
            <div class="dir-list" v-if="dirs.length">
              <button
                v-for="d in dirs"
                :key="d"
                class="dir-item"
                @click="browseDir(d)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <span>{{ d }}</span>
              </button>
            </div>
            <div class="dir-list" v-if="drives.length">
              <button
                v-for="d in drives"
                :key="d"
                class="dir-item"
                @click="browseDir(d)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8"/><path d="M12 17v4"/>
                </svg>
                <span>{{ d }}</span>
              </button>
            </div>
          </div>

          <div class="scan-actions">
            <button
              class="btn-scan-start"
              :disabled="!selectedDir || store.scanLoading"
              @click="startScan"
            >
              <span v-if="store.scanLoading" class="scanning">
                <span class="spinner"></span> 扫描中...
              </span>
              <span v-else>开始扫描</span>
            </button>
          </div>

          <div v-if="selectedDir" class="selected-dir">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            {{ selectedDir }}
          </div>

          <transition name="fade">
            <div v-if="scanResult" class="scan-result">
              <p>扫描完成，新增 {{ scanResult.added }} 张照片</p>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useGalleryStore } from '../stores/gallery'

const emit = defineEmits(['close'])
const store = useGalleryStore()

const currentPath = ref('')
const selectedDir = ref('')
const dirs = ref([])
const drives = ref([])
const scanResult = ref(null)

onMounted(async () => {
  const res = await fetch('/api/suggest-dirs')
  const data = await res.json()
  if (data.drives) drives.value = data.drives
})

async function browseDir(path) {
  currentPath.value = path
  selectedDir.value = path
  const res = await fetch(`/api/suggest-dirs?path=${encodeURIComponent(path)}`)
  const data = await res.json()
  if (data.directories) dirs.value = data.directories
}

async function startScan() {
  scanResult.value = null
  const result = await store.scanDirectory(selectedDir.value)
  scanResult.value = result
}
</script>

<style scoped>
.scan-panel {
  position: fixed;
  top: 64px;
  right: 0;
  width: 380px;
  max-height: calc(100vh - 64px);
  z-index: 99;
  background: var(--bg-primary);
  border-left: 1px solid var(--border);
  box-shadow: -8px 0 32px var(--shadow);
  overflow-y: auto;
}

.scan-inner {
  padding: 24px;
}

.scan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.scan-header h3 {
  font-family: 'Noto Serif SC', serif;
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-muted);
  cursor: pointer;
  line-height: 1;
}

.dir-input {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.dir-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: border-color 0.3s;
}

.dir-input input:focus {
  border-color: var(--accent);
}

.btn-go {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-go:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.dir-list {
  max-height: 240px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.dir-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  border-radius: 6px;
  text-align: left;
  transition: all 0.2s;
}

.dir-item:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.scan-actions {
  margin: 16px 0;
}

.btn-scan-start {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: var(--bg-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-scan-start:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-scan-start:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--bg-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.scanning {
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-dir {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-all;
  margin-bottom: 12px;
}

.scan-result {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}
</style>