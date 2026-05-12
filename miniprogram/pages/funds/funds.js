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
    try {
      const funds = await listFunds(1)
      // 预格式化展示字段
      const list = (funds || []).map(item => {
        const chg = Number(item.daily_change || 0)
        return {
          ...item,
          _navText: item.nav != null ? Number(item.nav).toFixed(4) : '--',
          _changeText: (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%',
          _changeClass: chg >= 0 ? 'amount-up' : 'amount-down',
        }
      })
      this.setData({ funds: list, loading: false })
    } catch (e) {
      console.error('加载基金列表失败:', e)
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
