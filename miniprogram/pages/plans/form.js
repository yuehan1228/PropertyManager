import { listFunds, listAccounts, getFund, createPlan, updatePlan } from '../../services/api'

Page({
  data: {
    editId: null,
    funds: [],
    accounts: [],
    form: {
      plan_name: '',
      fund_code: '',
      from_account_id: '',
      amount: '',
      frequency: 'monthly',
      execute_day: 1,
      total_rounds: '',
      start_date: '',
      remark: '',
    },
    submitting: false,
  },

  onLoad(options) {
    const today = new Date()
    this.setData({
      'form.start_date': this._fmtDate(today),
    })

    if (options.id) {
      this.setData({ editId: options.id })
      // 这里需要加载已有计划数据 —— 简化起见，从 plans 列表页传入
      // 实际项目中用 wx.getStorage 或重新拉取
    }

    this.loadOptions()
  },

  async loadOptions() {
    try {
      const [funds, accounts] = await Promise.all([
        listFunds(1),
        listAccounts(),
      ])
      this.setData({ funds, accounts })
    } catch (e) {
      // handled
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onPickerChange(e) {
    const field = e.currentTarget.dataset.field
    const idx = e.detail.value
    const list = field === 'fund_code' ? this.data.funds : this.data.accounts
    this.setData({
      [`form.${field}`]: list[idx]?.code || list[idx]?.id || '',
    })
  },

  onRadioChange(e) {
    this.setData({ 'form.frequency': e.detail.value })
  },

  async onSubmit() {
    const { form, editId } = this.data
    if (!form.plan_name.trim() || !form.fund_code || !form.from_account_id || !form.amount) {
      wx.showToast({ title: '请完善必填项', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      const payload = {
        plan_name: form.plan_name,
        fund_code: form.fund_code,
        from_account_id: Number(form.from_account_id),
        amount: parseFloat(form.amount),
        frequency: form.frequency,
        execute_day: Number(form.execute_day) || 1,
        total_rounds: form.total_rounds ? Number(form.total_rounds) : null,
        start_date: form.start_date,
        remark: form.remark,
      }

      if (editId) {
        await updatePlan(editId, payload)
      } else {
        await createPlan(payload)
      }
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1000)
    } catch (e) {
      this.setData({ submitting: false })
    }
  },

  _fmtDate(d) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  },
})
