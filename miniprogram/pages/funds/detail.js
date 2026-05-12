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
    try {
      const [fund, navHistory] = await Promise.all([
        getFund(this.data.code),
        getNavHistory(this.data.code, 30),
      ])
      // 预格式化
      const f = fund ? {
        ...fund,
        _nav: this._fmtNav(fund.nav),
        _accNav: this._fmtNav(fund.acc_nav),
        _change: this._fmtChange(fund.daily_change),
        _changeClass: (fund.daily_change || 0) >= 0 ? 'amount-up' : 'amount-down',
        _type: this._typeLabel(fund.fund_type),
      } : null
      const h = (navHistory || []).map(item => ({
        ...item,
        _nav: this._fmtNav(item.unit_nav),
        _change: this._fmtChange(item.daily_change),
        _changeClass: (item.daily_change || 0) >= 0 ? 'amount-up' : 'amount-down',
      }))
      this.setData({ fund: f, navHistory: h, loading: false })
    } catch (e) {
      console.error('加载基金详情失败:', e)
      this.setData({ loading: false })
    }
  },

  async onSyncFund() {
    try {
      await syncFund(this.data.code)
      wx.showToast({ title: '同步成功', icon: 'success' })
      this.loadData()
    } catch (e) { /* handled */ }
  },

  _typeLabel(type) {
    const map = { stock:'股票型', mixed:'混合型', bond:'债券型', money:'货币型', index:'指数型', qdii:'QDII', etf:'ETF联接', fof:'FOF' }
    return map[type] || type || '--'
  },
  _fmtNav(v) {
    if (v == null) return '--'
    return Number(v).toFixed(4)
  },
  _fmtChange(v) {
    if (v == null) return '0.00'
    const val = Number(v)
    return (val >= 0 ? '+' : '') + val.toFixed(2)
  },
})
