<template>
  <div class="admin-login">
    <div class="login-card">
      <div class="login-header">
        <span class="login-icon">栖</span>
        <h2>管理员登录</h2>
        <p>Perch 栖所</p>
      </div>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <input
            v-model="password"
            type="password"
            placeholder="密码"
            required
            autocomplete="current-password"
          />
        </div>
        <p v-if="error" class="login-error">{{ error }}</p>
        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>登 录</span>
        </button>
      </form>
      <router-link to="/" class="back-link">← 返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/admin/dashboard')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: var(--bg-primary);
}

.login-card {
  width: 360px;
  padding: 48px 36px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  text-align: center;
  animation: scale-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.login-header {
  margin-bottom: 32px;
}

.login-icon {
  display: inline-block;
  font-family: 'Noto Serif SC', serif;
  font-size: 40px;
  color: var(--accent);
  margin-bottom: 8px;
}

.login-header h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.login-header p {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.form-group {
  margin-bottom: 16px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.form-group input:focus {
  border-color: var(--accent);
}

.login-error {
  color: #c0392b;
  font-size: 13px;
  margin-bottom: 12px;
}

.login-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: var(--bg-primary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  letter-spacing: 4px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid var(--bg-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.back-link {
  display: inline-block;
  margin-top: 24px;
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.3s;
}

.back-link:hover {
  color: var(--accent);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}
</style>