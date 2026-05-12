import { login, devLogin } from '../../services/api'

const app = getApp()

Page({
  data: {
    loading: false,
    errorMsg: '',
  },

  onLoad() {
    // 如果已有 token，尝试直接跳转
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  async handleLogin() {
    if (this.data.loading) return
    this.setData({ loading: true, errorMsg: '' })

    try {
      wx.showLoading({ title: '登录中...', mask: true })

      // 1. 调用 wx.login 获取 code
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject,
        })
      })

      if (!loginRes.code) {
        throw new Error('获取登录凭证失败')
      }

      // 2. 发送 code 到后端
      const result = await login(loginRes.code)

      // 3. 保存 token 到本地
      wx.setStorageSync('token', result.token)
      wx.setStorageSync('userInfo', JSON.stringify({
        userId: result.user_id,
        openid: result.openid,
        nickname: result.nickname,
      }))

      app.globalData.token = result.token
      app.globalData.userInfo = {
        userId: result.user_id,
        openid: result.openid,
        nickname: result.nickname,
      }

      wx.hideLoading()
      wx.showToast({ title: result.is_new ? '欢迎来到资产追踪' : '登录成功', icon: 'success' })

      // 4. 跳转到首页
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 800)
    } catch (err) {
      wx.hideLoading()
      console.error('登录失败:', err)
      this.setData({
        loading: false,
        errorMsg: err.message || '登录失败，请重试',
      })
    }
  },

  // 开发模式：跳过微信登录直接使用测试账号
  async handleDevLogin() {
    if (this.data.loading) return
    this.setData({ loading: true, errorMsg: '' })

    try {
      wx.showLoading({ title: '开发登录中...', mask: true })

      const result = await devLogin('web_dev_user')

      wx.setStorageSync('token', result.token)
      wx.setStorageSync('userInfo', JSON.stringify({
        userId: result.user_id,
        openid: result.openid,
        nickname: result.nickname,
      }))

      app.globalData.token = result.token
      app.globalData.userInfo = {
        userId: result.user_id,
        openid: result.openid,
        nickname: result.nickname,
      }

      wx.hideLoading()
      wx.showToast({ title: '开发登录成功', icon: 'success' })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 800)
    } catch (err) {
      wx.hideLoading()
      this.setData({
        loading: false,
        errorMsg: err.message || '登录失败',
      })
    }
  },

  handleDevLoginInput() {
    // 可在此扩展手动输入 openid 进行开发测试
  },
})
