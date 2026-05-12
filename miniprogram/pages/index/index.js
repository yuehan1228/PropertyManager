import { getDashboard } from '../../services/api'

Page({
  data: {
    dashboard: null,
    loading: true,
    refreshTime: '',
    // 预格式化的展示字段，避免 WXML 中复杂表达式导致渲染错误
    dispTotalAssets: '0.00',
    dispDailyProfit: '0.00',
    dispCumulativeProfit: '0.00',
    dispTotalSavings: '0.00',
    dispTotalFundValue: '0.00',
    dispTotalPending: '0.00',
    dailyProfitClass: 'amount-up',
    cumulativeClass: 'amount-up',
    holdings: [],
  },

  onShow() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    try {
      const dashboard = await getDashboard()
      const h = dashboard.holdings || []

      this.setData({
        dashboard,
        loading: false,
        refreshTime: this._formatTime(new Date()),
        dispTotalAssets: this._fmt(dashboard.total_assets),
        dispDailyProfit: this._sign(dashboard.daily_profit) + this._fmt(Math.abs(dashboard.daily_profit)),
        dispCumulativeProfit: this._sign(dashboard.cumulative_profit) + this._fmt(Math.abs(dashboard.cumulative_profit)),
        dispTotalSavings: this._fmt(dashboard.total_savings),
        dispTotalFundValue: this._fmt(dashboard.total_fund_value),
        dispTotalPending: this._fmt(dashboard.total_pending || 0),
        dailyProfitClass: (dashboard.daily_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        cumulativeClass: (dashboard.cumulative_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        holdings: h.map(item => ({
          ...item,
          _value: this._fmt(item.current_value || 0),
          _profit: this._sign(item.daily_profit || 0) + this._fmt(Math.abs(item.daily_profit || 0)),
          _profitClass: (item.daily_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
          _shares: (item.total_shares || 0).toFixed(2),
        })),
      })
    } catch (e) {
      console.error('加载看板失败:', e)
      this.setData({ loading: false })
    }
  },

  // 跳转
  goAccounts() { wx.switchTab({ url: '/pages/accounts/accounts' }) },
  goFunds() { wx.switchTab({ url: '/pages/funds/funds' }) },
  goTransactions() { wx.navigateTo({ url: '/pages/transactions/transactions' }) },
  goHoldings() { wx.navigateTo({ url: '/pages/holdings/holdings' }) },

  // 内部格式化（不在 WXML 中调用，避免渲染层兼容问题）
  _fmt(v) {
    if (v == null || (typeof v === 'number' && isNaN(v))) return '0.00'
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  _sign(v) {
    v = v || 0
    return v >= 0 ? '+' : '-'
  },
  _formatTime(d) {
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${h}:${m}:${s}`
  },
})
