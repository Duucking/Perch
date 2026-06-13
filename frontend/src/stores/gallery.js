import { defineStore } from 'pinia'

export const useGalleryStore = defineStore('gallery', {
  state: () => ({
    photos: [],
    total: 0,
    page: 1,
    totalPages: 0,
    loading: false,
    scanLoading: false,
    stats: { total_photos: 0, total_size: 0, last_scan: null },
    darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
    searchQuery: '',
    perPage: 50
  }),

  actions: {
    toggleDarkMode() {
      this.darkMode = !this.darkMode
      this.applyTheme()
    },

    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.darkMode ? 'dark' : 'light')
    },

    async fetchPhotos() {
      this.loading = true
      try {
        const params = new URLSearchParams({
          page: this.page,
          per_page: this.perPage,
          sort: 'scanned_at',
          order: 'desc'
        })
        if (this.searchQuery) params.set('search', this.searchQuery)

        const res = await fetch(`/api/photos?${params}`)
        const data = await res.json()
        this.photos = data.photos
        this.total = data.total
        this.totalPages = data.total_pages
      } catch (e) {
        console.error('Failed to fetch photos:', e)
      } finally {
        this.loading = false
      }
    },

    async scanDirectory(directory) {
      this.scanLoading = true
      try {
        const res = await fetch('/api/scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ directory })
        })
        const data = await res.json()
        await this.fetchStats()
        await this.fetchPhotos()
        return data
      } finally {
        this.scanLoading = false
      }
    },

    async fetchStats() {
      try {
        const res = await fetch('/api/stats')
        this.stats = await res.json()
      } catch (e) {
        console.error('Failed to fetch stats:', e)
      }
    },

    setPage(p) {
      this.page = p
      this.fetchPhotos()
    },

    setSearch(q) {
      this.searchQuery = q
      this.page = 1
      this.fetchPhotos()
    }
  }
})