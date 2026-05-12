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
    try {
      const holdings = await listHoldings()
      const list = (holdings || []).map(item => ({
        ...item,
        _value: this._fmt(item.current_value),
        _profit: this._sign(item.daily_profit) + this._fmt(Math.abs(item.daily_profit || 0)),
        _profitClass: (item.daily_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        _totalShares: (item.total_shares || 0).toFixed(2),
        _available: (item.available_shares || 0).toFixed(2),
        _frozen: (item.frozen_shares || 0).toFixed(2),
        _costNav: item.avg_cost_nav != null ? Number(item.avg_cost_nav).toFixed(4) : '--',
        _totalProfit: this._sign(item.total_profit) + this._fmt(Math.abs(item.total_profit || 0)),
        _totalProfitClass: (item.total_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        _profitRate: (item.profit_rate || 0).toFixed(2),
      }))
      this.setData({ holdings: list, loading: false })
    } catch (e) {
      console.error('加载持仓失败:', e)
      this.setData({ loading: false })
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/holdings/detail?id=${id}` })
    }
  },

  _fmt(v) {
    if (v == null || (typeof v === 'number' && isNaN(v))) return '0.00'
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  _sign(v) {
    v = v || 0
    return v >= 0 ? '+' : '-'
  },
})
