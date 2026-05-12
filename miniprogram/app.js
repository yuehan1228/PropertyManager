App({
  globalData: {
    baseUrl: 'https://rated-vegetables-airfare-amber.trycloudflare.com', // cloudflared 隧道（重启会变）
    token: null,
    userInfo: null,
  },

  onLaunch() {
    // 恢复后端地址
    const savedUrl = wx.getStorageSync('baseUrl')
    if (savedUrl) {
      this.globalData.baseUrl = savedUrl
    }

    // 恢复登录态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      try {
        this.globalData.userInfo = JSON.parse(userInfo)
      } catch (e) { /* ignore */ }
    }
  },

  onShow(options) {
    // 仅在非登录页时检查登录态
    const scene = options?.scene
    const path = options?.path
    if (path && path.startsWith('pages/login')) return

    const token = this.globalData.token || wx.getStorageSync('token')
    if (!token) {
      // 延迟跳转，避免与冷启动竞态
      setTimeout(() => {
        wx.reLaunch({ url: '/pages/login/login' })
      }, 300)
    }
  },

  setBaseUrl(url) {
    this.globalData.baseUrl = url
    wx.setStorageSync('baseUrl', url)
  },

  logout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    this.globalData.token = null
    this.globalData.userInfo = null
    wx.reLaunch({ url: '/pages/login/login' })
  },
})
