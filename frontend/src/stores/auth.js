import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('perch_token') || '',
    user: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    displayName: (state) => state.user?.display_name || state.user?.username || ''
  },

  actions: {
    async login(username, password) {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || '登录失败')
      }
      const data = await res.json()
      this.token = data.token
      this.user = data.user
      localStorage.setItem('perch_token', data.token)
      return data
    },

    async restore() {
      if (!this.token) return
      try {
        const res = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        if (!res.ok) throw new Error('Session expired')
        this.user = await res.json()
      } catch {
        this.logout()
      }
    },

    async updateProfile(data) {
      const res = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`
        },
        body: JSON.stringify(data)
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || '更新失败')
      }
      this.user = await res.json()
    },

    async scanDirectory(directory) {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`
        },
        body: JSON.stringify({ directory })
      })
      if (!res.ok) throw new Error('扫描请求失败')
      return res.json()
    },

    async deletePhoto(photoId) {
      const res = await fetch(`/api/photos/${photoId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${this.token}` }
      })
      if (!res.ok) throw new Error('删除失败')
    },

    async fetchSuggestDirs(path) {
      const res = await fetch(`/api/suggest-dirs?path=${encodeURIComponent(path)}`, {
        headers: { Authorization: `Bearer ${this.token}` }
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },

    logout() {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${this.token}` }
      }).catch(() => {})
      this.token = ''
      this.user = null
      localStorage.removeItem('perch_token')
    }
  }
})