<template>
  <div class="admin-dashboard">
    <aside class="admin-sidebar">
      <div class="sidebar-user">
        <span class="user-avatar">{{ auth.displayName.charAt(0) }}</span>
        <span class="user-name">{{ auth.displayName }}</span>
        <span class="user-role">管理员</span>
      </div>
      <nav class="sidebar-nav">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['nav-item', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          <span v-html="tab.icon"></span>
          {{ tab.label }}
        </button>
      </nav>
      <button class="btn-logout" @click="handleLogout">退出登录</button>
    </aside>

    <main class="admin-main">
      <!-- Photos tab -->
      <div v-if="activeTab === 'photos'" class="tab-content">
        <div class="tab-header">
          <h2>照片管理</h2>
          <div class="photo-actions">
            <div class="search-box">
              <input v-model="searchQuery" placeholder="搜索文件名..." @input="onSearch" />
            </div>
            <span class="photo-total">{{ galleryStore.total }} 张</span>
          </div>
        </div>
        <div class="photo-table">
          <div class="table-header">
            <span class="col-thumb"></span>
            <span class="col-name">文件名</span>
            <span class="col-desc">简介</span>
            <span class="col-size">大小</span>
            <span class="col-dims">尺寸</span>
            <span class="col-action"></span>
          </div>
          <div v-for="photo in galleryStore.photos" :key="photo.id" class="table-row">
            <span class="col-thumb">
              <img :src="getThumbUrl(photo.thumbnail_path)" :alt="photo.filename" />
            </span>
            <span class="col-name" :title="photo.filename">{{ photo.filename }}</span>
            <span class="col-desc">
              <div class="desc-display" v-if="editingId !== photo.id">
                <span class="desc-text" :class="{ empty: !photo.description }" @click="startEdit(photo)">{{ photo.description || '添加简介...' }}</span>
              </div>
              <div class="desc-editing" v-else>
                <textarea v-model="editText" rows="2" placeholder="为这张照片写一段故事..." class="desc-input" @keydown.escape="cancelEdit"></textarea>
                <div class="desc-actions">
                  <button class="btn-save-desc" @click="saveDesc(photo)">保存</button>
                  <button class="btn-cancel-desc" @click="cancelEdit">取消</button>
                </div>
              </div>
            </span>
            <span class="col-size">{{ formatSize(photo.file_size) }}</span>
            <span class="col-dims">{{ photo.width }}×{{ photo.height }}</span>
            <span class="col-action">
              <button class="btn-delete" @click="confirmDelete(photo)">删除</button>
            </span>
          </div>
        </div>
        <div v-if="galleryStore.totalPages > 1" class="table-pagination">
          <button :disabled="galleryStore.page <= 1" @click="galleryStore.setPage(galleryStore.page - 1)" class="page-btn">←</button>
          <span class="page-info">{{ galleryStore.page }} / {{ galleryStore.totalPages }}</span>
          <button :disabled="galleryStore.page >= galleryStore.totalPages" @click="galleryStore.setPage(galleryStore.page + 1)" class="page-btn">→</button>
        </div>
      </div>

      <!-- Scan tab -->
      <div v-if="activeTab === 'scan'" class="tab-content">
        <div class="tab-header">
          <h2>目录扫描</h2>
        </div>
        <div class="scan-body">
          <div class="scan-form">
            <label class="scan-label">图片存放路径</label>
            <input v-model="scanPath" type="text" placeholder="例如: /mnt/photos 或 /home/user/Pictures" class="scan-path-input" />
            <p class="scan-hint">输入服务器上存放照片的目录完整路径，系统将递归扫描该目录下的所有图片</p>
            <button class="btn-scan-start" :disabled="!scanPath || scanning" @click="startScan">
              <span v-if="scanning" class="scanning"><span class="spinner"></span> 扫描中...</span>
              <span v-else>开始扫描</span>
            </button>
          </div>
          <div v-if="scanResult" class="scan-result">{{ scanResult }}</div>
        </div>
      </div>

      <!-- Profile tab -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        <div class="tab-header">
          <h2>账户设置</h2>
        </div>
        <div class="profile-form">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="profile.username" type="text" disabled />
          </div>
          <div class="form-group">
            <label>显示名称</label>
            <input v-model="profile.displayName" type="text" placeholder="修改显示名称" />
          </div>
          <div class="form-divider"></div>
          <div class="form-group">
            <label>原密码</label>
            <input v-model="profile.oldPassword" type="password" placeholder="输入原密码" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="profile.newPassword" type="password" placeholder="输入新密码" />
          </div>
          <p v-if="profileError" class="form-error">{{ profileError }}</p>
          <p v-if="profileSuccess" class="form-success">{{ profileSuccess }}</p>
          <button class="btn-save" @click="saveProfile" :disabled="profileSaving">
            <span v-if="profileSaving" class="spinner"></span>
            <span v-else>保存修改</span>
          </button>
        </div>
      </div>
    </main>

    <div v-if="deleteTarget" class="modal-overlay" @click="deleteTarget = null">
      <div class="modal-card" @click.stop>
        <p>确认删除 <strong>{{ deleteTarget.filename }}</strong>？</p>
        <p class="modal-hint">此操作不可撤销</p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="deleteTarget = null">取消</button>
          <button class="btn-confirm-delete" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useGalleryStore } from '../stores/gallery'

const auth = useAuthStore()
const galleryStore = useGalleryStore()
const router = useRouter()

const activeTab = ref('photos')
const searchQuery = ref('')
const editingId = ref(null)
const editText = ref('')
let searchTimer = null

// Scan
const scanPath = ref('')
const scanning = ref(false)
const scanResult = ref('')

// Profile
const profile = ref({ username: '', displayName: '', oldPassword: '', newPassword: '' })
const profileError = ref('')
const profileSuccess = ref('')
const profileSaving = ref(false)

// Delete
const deleteTarget = ref(null)

const tabs = [
  { key: 'photos', label: '照片管理', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>' },
  { key: 'scan', label: '扫描目录', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/><path d="M11 8v6"/></svg>' },
  { key: 'profile', label: '账户设置', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' }
]

onMounted(async () => {
  if (!auth.isAdmin) {
    router.replace('/admin')
    return
  }
  galleryStore.fetchPhotos()
  profile.value.username = auth.user?.username || ''
  profile.value.displayName = auth.user?.display_name || ''
})

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => galleryStore.setSearch(searchQuery.value), 400)
}

function getThumbUrl(path) {
  if (!path) return ''
  const parts = path.replace(/\\/g, '/').split('/')
  return `/api/thumbnails/${parts[parts.length - 1]}`
}

function formatSize(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

function startEdit(photo) {
  editingId.value = photo.id
  editText.value = photo.description || ''
}

function cancelEdit() {
  editingId.value = null
  editText.value = ''
}

async function saveDesc(photo) {
  try {
    const res = await fetch(`/api/photos/${photo.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token}`
      },
      body: JSON.stringify({ description: editText.value.trim() })
    })
    if (!res.ok) throw new Error('保存失败')
    photo.description = editText.value.trim()
    editingId.value = null
  } catch (e) {
    alert('保存失败：' + e.message)
  }
}

async function startScan() {
  scanning.value = true
  scanResult.value = ''
  try {
    const result = await auth.scanDirectory(scanPath.value.trim())
    scanResult.value = `扫描完成，新增 ${result.added} 张照片`
    galleryStore.fetchStats()
    galleryStore.fetchPhotos()
  } catch (e) {
    scanResult.value = '扫描失败：' + e.message
  } finally {
    scanning.value = false
  }
}

function confirmDelete(photo) {
  deleteTarget.value = photo
}

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await auth.deletePhoto(deleteTarget.value.id)
    galleryStore.fetchPhotos()
    galleryStore.fetchStats()
  } catch (e) {
    alert('删除失败')
  }
  deleteTarget.value = null
}

async function saveProfile() {
  profileError.value = ''
  profileSuccess.value = ''
  profileSaving.value = true
  try {
    const data = {}
    if (profile.value.displayName && profile.value.displayName !== auth.user?.display_name) {
      data.display_name = profile.value.displayName
    }
    if (profile.value.oldPassword && profile.value.newPassword) {
      data.old_password = profile.value.oldPassword
      data.new_password = profile.value.newPassword
    }
    if (Object.keys(data).length === 0) {
      profileError.value = '没有需要修改的内容'
      return
    }
    await auth.updateProfile(data)
    profile.value.oldPassword = ''
    profile.value.newPassword = ''
    profileSuccess.value = '保存成功'
  } catch (e) {
    profileError.value = e.message
  } finally {
    profileSaving.value = false
  }
}

function handleLogout() {
  auth.logout()
  router.push('/admin')
}
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  min-height: calc(100vh - 64px);
  background: var(--bg-primary);
}

.admin-sidebar {
  width: 200px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  min-height: 100%;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-user {
  text-align: center;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--bg-primary);
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.user-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 11px;
  color: var(--text-muted);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-logout {
  margin-top: 16px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-logout:hover {
  border-color: #c0392b;
  color: #c0392b;
}

.admin-main {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.tab-header h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.photo-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-box input {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  width: 200px;
}

.search-box input:focus {
  border-color: var(--accent);
}

.photo-total {
  font-size: 13px;
  color: var(--text-muted);
}

.photo-table {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 48px 1fr 1.5fr 80px 80px 60px;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
}

.table-header {
  background: var(--bg-secondary);
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-row {
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-primary);
  transition: background 0.2s;
}

.table-row:hover {
  background: var(--bg-card);
}

.col-thumb img {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
}

.col-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-desc {
  min-width: 0;
}

.desc-display {
  cursor: pointer;
}

.desc-text {
  display: block;
  font-family: 'Noto Serif SC', 'SimSun', '宋体', serif;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 0;
  transition: color 0.2s;
}

.desc-text.empty {
  color: var(--text-muted);
  font-style: italic;
}

.desc-text:hover {
  color: var(--accent);
}

.desc-editing {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.desc-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-family: 'Noto Serif SC', 'SimSun', '宋体', serif;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 50px;
}

.desc-input:focus {
  box-shadow: 0 0 0 2px var(--shadow);
}

.desc-actions {
  display: flex;
  gap: 6px;
}

.btn-save-desc,
.btn-cancel-desc {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-desc {
  border: none;
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-save-desc:hover {
  background: var(--accent-hover);
}

.btn-cancel-desc {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
}

.btn-cancel-desc:hover {
  border-color: var(--text-muted);
}

.col-size,
.col-dims,
.col-date {
  color: var(--text-secondary);
  font-size: 12px;
}

.btn-delete {
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  border-color: #c0392b;
  color: #c0392b;
}

.table-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}

.page-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: var(--text-muted);
}

/* Scan tab */
.scan-body {
  max-width: 520px;
}

.scan-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scan-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.scan-path-input {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 14px;
  font-family: 'Inter', monospace;
  outline: none;
  transition: border-color 0.3s;
}

.scan-path-input:focus {
  border-color: var(--accent);
}

.scan-hint {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
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
  transition: all 0.3s;
  margin-top: 4px;
}

.btn-scan-start:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-scan-start:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.scanning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--bg-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.scan-result {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}

/* Profile tab */
.profile-form {
  max-width: 400px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.form-group input:focus {
  border-color: var(--accent);
}

.form-group input:disabled {
  opacity: 0.5;
}

.form-divider {
  height: 1px;
  background: var(--border);
  margin: 24px 0;
}

.form-error {
  color: #c0392b;
  font-size: 13px;
  margin-bottom: 12px;
}

.form-success {
  color: #27ae60;
  font-size: 13px;
  margin-bottom: 12px;
}

.btn-save {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: var(--bg-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-save:disabled {
  opacity: 0.6;
}

/* Delete modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  animation: fade-in 0.2s;
}

.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  animation: scale-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-card p {
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.modal-hint {
  font-size: 12px !important;
  color: var(--text-muted) !important;
  margin-bottom: 20px !important;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-cancel,
.btn-confirm-delete {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  border-color: var(--accent);
}

.btn-confirm-delete {
  border: none;
  background: #c0392b;
  color: #fff;
}

.btn-confirm-delete:hover {
  background: #a93226;
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>