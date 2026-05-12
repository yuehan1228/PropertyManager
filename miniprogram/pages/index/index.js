import { getDashboard } from '../../services/api'

Page({
  data: {
    dashboard: null,
    loading: true,
    refreshTime: '',
  },

  onShow() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const dashboard = await getDashboard()
      this.setData({
        dashboard,
        loading: false,
        refreshTime: this._formatTime(new Date()),
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  // 跳转
  goAccounts() {
    wx.switchTab({ url: '/pages/accounts/accounts' })
  },
  goFunds() {
    wx.switchTab({ url: '/pages/funds/funds' })
  },
  goTransactions() {
    wx.navigateTo({ url: '/pages/transactions/transactions' })
  },
  goHoldings() {
    wx.navigateTo({ url: '/pages/holdings/holdings' })
  },

  // 格式化
  fmt(money) {
    if (money == null) return '--'
    return Number(money).toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  },
  sign(money) {
    return money >= 0 ? '+' : ''
  },

  _formatTime(d) {
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${h}:${m}:${s}`
  },
})
