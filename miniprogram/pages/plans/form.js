import { listFunds, listAccounts, createPlan, updatePlan } from '../../services/api'

Page({
  data: {
    editId: null,
    funds: [],
    accounts: [],
    // 预计算数组（WXML 不支持内联数组）
    freqOptions: [
      { value: 'monthly', label: '每月' },
      { value: 'biweekly', label: '每两周' },
      { value: 'weekly', label: '每周' },
      { value: 'daily', label: '每日' },
    ],
    dayOptions: [1, 5, 10, 15, 20, 25, 28],
    // 表单
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
    // WXML 展示用的预计算文本
    selectedFundDisplay: '请选择基金',
    selectedAccountDisplay: '请选择账户',
    submitting: false,
  },

  onLoad(options) {
    const today = new Date()
    this.setData({ 'form.start_date': this._fmtDate(today) })
    if (options.id) {
      this.setData({ editId: options.id })
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
      // handled by api layer
    }
  },

  // ---------- 输入事件 ----------
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  // ---------- picker 选择 ----------
  onFundPickerChange(e) {
    const idx = e.detail.value
    const fund = this.data.funds[idx]
    if (fund) {
      this.setData({
        'form.fund_code': fund.code,
        selectedFundDisplay: fund.code + ' ' + (fund.name || ''),
      })
    }
  },

  onAccountPickerChange(e) {
    const idx = e.detail.value
    const account = this.data.accounts[idx]
    if (account) {
      this.setData({
        'form.from_account_id': account.id,
        selectedAccountDisplay: account.label,
      })
    }
  },

  onDayPickerChange(e) {
    const idx = e.detail.value
    this.setData({ 'form.execute_day': this.data.dayOptions[idx] })
  },

  onRadioChange(e) {
    this.setData({ 'form.frequency': e.detail.value })
  },

  // ---------- 提交 ----------
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

  // ---------- 工具 ----------
  _fmtDate(d) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  },
})
