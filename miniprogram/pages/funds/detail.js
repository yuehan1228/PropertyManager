import { getFund, getNavHistory, syncFund } from '../../services/api'

Page({
  data: {
    code: '',
    fund: null,
    navHistory: [],
    loading: true,
  },

  onLoad(options) {
    if (options.code) {
      this.setData({ code: options.code })
      this.loadData()
    }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [fund, navHistory] = await Promise.all([
        getFund(this.data.code),
        getNavHistory(this.data.code, 30),
      ])
      this.setData({ fund, navHistory, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async onSyncFund() {
    try {
      await syncFund(this.data.code)
      wx.showToast({ title: '同步成功', icon: 'success' })
      this.loadData()
    } catch (e) {
      // error handled by api layer
    }
  },

  // 基金类型 → 中文
  typeLabel(type) {
    const map = {
      stock: '股票型', mixed: '混合型', bond: '债券型',
      money: '货币型', index: '指数型', qdii: 'QDII',
      etf: 'ETF联接', fof: 'FOF',
    }
    return map[type] || type || '--'
  },

  fmtNav(v) {
    if (v == null) return '--'
    return Number(v).toFixed(4)
  },
  fmtChange(v) {
    if (v == null) return '0.00'
    return (v >= 0 ? '+' : '') + Number(v).toFixed(2)
  },
})
