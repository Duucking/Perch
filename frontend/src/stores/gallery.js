import { defineStore } from 'pinia'

export const useGalleryStore = defineStore('gallery', {
  state: () => ({
    photos: [],
    total: 0,
    totalPages: 0,
    page: 1,
    loading: false,
    loadingMore: false,
    allLoaded: false,
    stats: { total_photos: 0, total_size: 0, last_scan: null },
    darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
    searchQuery: '',
    cols: 4,
    perPageAdmin: 50
  }),

  actions: {
    toggleDarkMode() {
      this.darkMode = !this.darkMode
      this.applyTheme()
    },

    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.darkMode ? 'dark' : 'light')
    },

    setCols(n) {
      this.cols = n
    },

    async fetchPhotos() {
      this.loading = true
      this.allLoaded = false
      this.page = 1
      try {
        const params = new URLSearchParams({
          page: 1,
          per_page: this.cols * 5,
          sort: 'scanned_at',
          order: 'desc'
        })
        if (this.searchQuery) params.set('search', this.searchQuery)

        const res = await fetch(`/api/photos?${params}`)
        const data = await res.json()
        const fetched = data.photos || []
        this.photos = fetched
        this.total = data.total
        if (fetched.length >= data.total) {
          this.allLoaded = true
        }
      } catch (e) {
        console.error('Failed to fetch photos:', e)
      } finally {
        this.loading = false
      }
    },

    async loadMore() {
      if (this.loadingMore || this.allLoaded) return
      if (this.photos.length >= this.total) {
        this.allLoaded = true
        return
      }
      this.loadingMore = true
      this.page += 1
      try {
        const params = new URLSearchParams({
          page: this.page,
          per_page: this.cols * 2,
          sort: 'scanned_at',
          order: 'desc'
        })
        if (this.searchQuery) params.set('search', this.searchQuery)

        const res = await fetch(`/api/photos?${params}`)
        const data = await res.json()
        const newPhotos = (data.photos || []).filter(
          p => !this.photos.some(existing => existing.id === p.id)
        )
        this.photos = [...this.photos, ...newPhotos]
        this.total = data.total
        if (!newPhotos.length || this.photos.length >= this.total) {
          this.allLoaded = true
        }
      } catch (e) {
        this.page -= 1
        console.error('Failed to load more:', e)
      } finally {
        this.loadingMore = false
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

    setSearch(q) {
      this.searchQuery = q
      this.fetchPhotos()
    },

    async fetchAdminPhotos(page = 1) {
      this.loading = true
      this.page = page
      try {
        const params = new URLSearchParams({
          page,
          per_page: this.perPageAdmin,
          sort: 'scanned_at',
          order: 'desc'
        })
        if (this.searchQuery) params.set('search', this.searchQuery)

        const res = await fetch(`/api/photos?${params}`)
        const data = await res.json()
        this.photos = data.photos || []
        this.total = data.total
        this.totalPages = data.total_pages || 1
      } catch (e) {
        console.error('Failed to fetch admin photos:', e)
      } finally {
        this.loading = false
      }
    },

    setAdminPage(p) {
      if (p < 1 || p > this.totalPages) return
      this.fetchAdminPhotos(p)
    }
  }
})