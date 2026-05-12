import { listFunds } from '../../services/api'

Page({
  data: {
    funds: [],
    loading: true,
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
      const funds = await listFunds(1)
      this.setData({ funds, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  goDetail(e) {
    const code = e.detail.code
    wx.navigateTo({ url: `/pages/funds/detail?code=${code}` })
  },

  goAddFund() {
    wx.navigateTo({ url: '/pages/add-fund/add-fund' })
  },
})
