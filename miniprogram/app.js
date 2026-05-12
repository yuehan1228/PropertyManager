App({
  globalData: {
    baseUrl: 'http://localhost:8000', // 开发环境，发布时改生产地址
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
