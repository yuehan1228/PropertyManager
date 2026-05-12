import { listTransactions, deleteTransaction } from '../../services/api'

Page({
  data: {
    transactions: [],
    loading: true,
    filter: { fund_code: '', status: '', trans_type: '' },
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const params = {}
      if (this.data.filter.fund_code) params.fund_code = this.data.filter.fund_code
      if (this.data.filter.status) params.status = this.data.filter.status
      if (this.data.filter.trans_type) params.trans_type = this.data.filter.trans_type
      const transactions = await listTransactions(params)
      this.setData({ transactions, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  onFilterChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`filter.${field}`]: e.detail.value }, () => this.loadData())
  },

  async onDelete(e) {
    const id = e.currentTarget.dataset.id
    const confirm = await this._showConfirm('确定删除此交易？')
    if (!confirm) return
    try {
      await deleteTransaction(id)
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadData()
    } catch (e) { /* handled */ }
  },

  typeLabel(t) {
    const map = { buy: '买入', sell: '卖出', auto_buy: '定投买入', dividend: '分红', split: '拆分' }
    return map[t] || t
  },

  statusLabel(s) {
    const map = { pending: '待确认', confirmed: '已确认', settled: '已到账', cancelled: '已取消' }
    return map[s] || s
  },

  fmt(m) {
    return Number(m).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },

  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
