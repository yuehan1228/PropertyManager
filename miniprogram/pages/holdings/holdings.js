import { listHoldings } from '../../services/api'

Page({
  data: {
    holdings: [],
    loading: true,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const holdings = await listHoldings()
      this.setData({ holdings, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  goFund(e) {
    const code = e.currentTarget.dataset.code
    if (code) {
      wx.navigateTo({ url: `/pages/funds/detail?code=${code}` })
    }
  },

  fmt(money) {
    if (money == null) return '--'
    return Number(money).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  sign(money) {
    return money >= 0 ? '+' : ''
  },
})
