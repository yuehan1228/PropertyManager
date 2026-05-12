import { listPlans, createPlan, updatePlan, deletePlan } from '../../services/api'
import { listFunds } from '../../services/api'
import { listAccounts } from '../../services/api'

Page({
  data: {
    plans: [],
    loading: true,
    tab: 'active', // active | all
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const status = this.data.tab === 'active' ? 'active' : undefined
      const plans = await listPlans(status)
      this.setData({ plans, loading: false })
    } catch (e) {
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
    } catch (e) {
      // handled
    }
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

  freqLabel(f) {
    const map = { daily: '日', weekly: '周', biweekly: '双周', monthly: '月' }
    return map[f] || f
  },

  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
