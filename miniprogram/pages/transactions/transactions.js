import { listTransactions, deleteTransaction } from '../../services/api'

Page({
  data: {
    transactions: [],
    loading: true,
    typeOptions: ['全部', '买入', '卖出', '定投买入'],
    typeValues: ['', 'buy', 'sell', 'auto_buy'],
    statusOptions: ['全部', '待确认', '已确认', '已到账'],
    statusValues: ['', 'pending', 'confirmed', 'settled'],
    typeIndex: 0,
    statusIndex: 0,
    filter: { trans_type: '', status: '' },
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const params = { limit: 50 }
      if (this.data.filter.trans_type) params.trans_type = this.data.filter.trans_type
      if (this.data.filter.status) params.status = this.data.filter.status
      const transactions = await listTransactions(params)
      const list = (transactions || []).map(item => ({
        ...item,
        _amount: Number(item.amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        _shares: item.shares != null ? Number(item.shares).toFixed(2) : '',
        _typeLabel: this._typeLabel(item.trans_type),
        _statusLabel: this._statusLabel(item.status),
        _statusClass: item.status === 'settled' ? 'tag-green' : item.status === 'confirmed' ? 'tag-blue' : 'tag-yellow',
        _icon: item.trans_type === 'buy' || item.trans_type === 'auto_buy' ? '📥' : '📤',
      }))
      this.setData({ transactions: list, loading: false })
    } catch (e) {
      console.error('加载交易记录失败:', e)
      this.setData({ loading: false })
    }
  },

  onTypeFilterChange(e) {
    const idx = Number(e.detail.value)
    this.setData({
      typeIndex: idx,
      'filter.trans_type': this.data.typeValues[idx],
    }, () => this.loadData())
  },

  onStatusFilterChange(e) {
    const idx = Number(e.detail.value)
    this.setData({
      statusIndex: idx,
      'filter.status': this.data.statusValues[idx],
    }, () => this.loadData())
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

  _typeLabel(t) {
    const map = { buy: '买入', sell: '卖出', auto_buy: '定投买入', dividend: '分红', split: '拆分' }
    return map[t] || t
  },

  _statusLabel(s) {
    const map = { pending: '待确认', confirmed: '已确认', settled: '已到账', cancelled: '已取消' }
    return map[s] || s
  },

  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
