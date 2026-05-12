import { listPlans, listHoldings, listTransactions, updatePlan, deletePlan } from '../../services/api'

Page({
  data: {
    plans: [],
    loading: true,
    tab: 'active',
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const status = this.data.tab === 'active' ? 'active' : undefined
      const [plans, holdings, pendingTxns] = await Promise.all([
        listPlans(status),
        listHoldings(),
        listTransactions({ status: 'pending', limit: 200 }),
      ])

      // 建立持仓映射: fund_code → holding
      const holdingMap = {}
      for (const h of holdings) {
        holdingMap[h.fund_code] = h
      }

      // 建立待确认金额映射: fund_code → total_amount
      const pendingMap = {}
      for (const t of pendingTxns) {
        pendingMap[t.fund_code] = (pendingMap[t.fund_code] || 0) + (t.amount || 0)
      }

      const list = (plans || []).map(item => {
        const holding = holdingMap[item.fund_code]
        const pendingAmt = pendingMap[item.fund_code] || 0
        return {
          ...item,
          _amount: Number(item.amount || 0).toFixed(2),
          _freq: this._freqLabel(item.frequency),
          _statusLabel: item.status === 'active' ? '运行中' : item.status === 'paused' ? '已暂停' : '已停止',
          _statusClass: item.status === 'active' ? 'tag-green' : item.status === 'paused' ? 'tag-yellow' : 'tag-gray',
          _progress: `已完成 ${item.completed_rounds || 0}${item.total_rounds ? '/' + item.total_rounds : ''} 期`,
          // 持仓信息
          _holdValue: holding ? this._fmt(holding.current_value) : '--',
          _holdShares: holding ? Number(holding.total_shares || 0).toFixed(2) : '--',
          _hasHold: !!holding,
          // 待确定金额
          _pendingAmt: this._fmt(pendingAmt),
          _hasPending: pendingAmt > 0,
        }
      })
      this.setData({ plans: list, loading: false })
    } catch (e) {
      console.error('加载定投计划失败:', e)
      this.setData({ loading: false })
    }
  },

  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ tab }, () => this.loadData())
  },

  goForm(e) {
    const id = e.currentTarget?.dataset?.id
    const url = id ? `/pages/plans/form?id=${id}` : '/pages/plans/form'
    wx.navigateTo({ url })
  },

  async onToggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    const newStatus = status === 'active' ? 'paused' : 'active'
    try {
      await updatePlan(id, { status: newStatus })
      wx.showToast({ title: newStatus === 'active' ? '已启用' : '已暂停', icon: 'success' })
      this.loadData()
    } catch (e) { /* handled */ }
  },

  async onDelete(e) {
    const id = e.currentTarget.dataset.id
    const confirm = await this._showConfirm('确定删除此定投计划？')
    if (!confirm) return
    try {
      await deletePlan(id)
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadData()
    } catch (e) { /* handled */ }
  },

  _fmt(v) {
    if (v == null || (typeof v === 'number' && isNaN(v))) return '0.00'
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  _freqLabel(f) {
    const map = { daily: '日', weekly: '周', biweekly: '双周', monthly: '月' }
    return map[f] || f
  },
  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
