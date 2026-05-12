import { getHolding, updateHolding } from '../../services/api'

Page({
  data: {
    holding: null,
    loading: true,
    editing: false,
    form: {
      total_shares: '',
      available_shares: '',
      frozen_shares: '',
      total_cost: '',
      avg_cost_nav: '',
    },
    submitting: false,
  },

  onLoad(options) {
    if (options.id) {
      this.loadHolding(Number(options.id))
    }
  },

  async loadHolding(id) {
    try {
      const holding = await getHolding(id)
      const h = {
        ...holding,
        _value: this._fmt(holding.current_value),
        _profit: this._sign(holding.daily_profit) + this._fmt(Math.abs(holding.daily_profit || 0)),
        _profitClass: (holding.daily_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        _totalShares: Number(holding.total_shares || 0).toFixed(2),
        _available: Number(holding.available_shares || 0).toFixed(2),
        _frozen: Number(holding.frozen_shares || 0).toFixed(2),
        _costNav: holding.avg_cost_nav != null ? Number(holding.avg_cost_nav).toFixed(4) : '--',
        _totalCost: this._fmt(holding.total_cost),
        _totalProfit: this._sign(holding.total_profit) + this._fmt(Math.abs(holding.total_profit || 0)),
        _totalProfitClass: (holding.total_profit || 0) >= 0 ? 'amount-up' : 'amount-down',
        _profitRate: Number(holding.profit_rate || 0).toFixed(2),
      }
      this.setData({
        holding: h,
        loading: false,
        form: {
          total_shares: String(holding.total_shares || ''),
          available_shares: String(holding.available_shares || ''),
          frozen_shares: String(holding.frozen_shares || ''),
          total_cost: String(holding.total_cost || ''),
          avg_cost_nav: holding.avg_cost_nav != null ? String(holding.avg_cost_nav) : '',
        },
      })
    } catch (e) {
      console.error('加载持仓失败:', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  toggleEdit() {
    this.setData({ editing: !this.data.editing })
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  async onSaveEdit() {
    const { form, holding } = this.data
    this.setData({ submitting: true })
    try {
      await updateHolding(holding.id, {
        total_shares: parseFloat(form.total_shares) || 0,
        available_shares: parseFloat(form.available_shares) || 0,
        frozen_shares: parseFloat(form.frozen_shares) || 0,
        total_cost: parseFloat(form.total_cost) || 0,
        avg_cost_nav: form.avg_cost_nav ? parseFloat(form.avg_cost_nav) : null,
      })
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.setData({ editing: false })
      this.loadHolding(holding.id)
    } catch (e) {
      this.setData({ submitting: false })
    }
  },

  // 快捷操作
  goBuy() {
    const h = this.data.holding
    if (!h) return
    wx.navigateTo({
      url: `/pages/transactions/transactions?action=buy&code=${h.fund_code}&name=${encodeURIComponent(h.fund_name || '')}`,
    })
  },
  goSell() {
    const h = this.data.holding
    if (!h) return
    wx.navigateTo({
      url: `/pages/transactions/transactions?action=sell&code=${h.fund_code}&name=${encodeURIComponent(h.fund_name || '')}`,
    })
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
