App({
  globalData: {
    baseUrl: 'https://concrete-cream-column-juan.trycloudflare.com', // cloudflared 隧道（重启会变）
    userInfo: null,
  },

  onLaunch() {
    // 检查存储的后端地址
    const savedUrl = wx.getStorageSync('baseUrl')
    if (savedUrl) {
      this.globalData.baseUrl = savedUrl
    }
  },

  setBaseUrl(url) {
    this.globalData.baseUrl = url
    wx.setStorageSync('baseUrl', url)
  },
})
