import { listFunds, listAccounts, listHoldings, listTransactions, createPlan, updatePlan } from '../../services/api'

Page({
  data: {
    editId: null,
    funds: [],
    accounts: [],
    freqOptions: [
      { value: 'monthly', label: '每月' },
      { value: 'biweekly', label: '每两周' },
      { value: 'weekly', label: '每周' },
      { value: 'daily', label: '每日' },
    ],
    dayOptions: [1, 5, 10, 15, 20, 25, 28],
    form: {
      fund_code: '',
      from_account_id: '',
      amount: '',
      frequency: 'monthly',
      execute_day: 1,
      total_rounds: '',
      start_date: '',
      remark: '',
    },
    selectedFundDisplay: '请选择基金',
    selectedAccountDisplay: '请选择账户',
    // 选中基金的持仓概览
    fundSummary: null, // { totalCost, currentValue, totalShares, pendingAmt }
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
      const [funds, allAccounts] = await Promise.all([
        listFunds(1),
        listAccounts(),
      ])
      // 定投扣款仅限银行卡
      const accounts = allAccounts.filter(a => a.account_type !== 'fund')
      this.setData({ funds, accounts })
    } catch (e) { /* handled */ }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  async onFundPickerChange(e) {
    const idx = e.detail.value
    const fund = this.data.funds[idx]
    if (fund) {
      this.setData({
        'form.fund_code': fund.code,
        selectedFundDisplay: fund.code + ' ' + (fund.name || ''),
        fundSummary: null,
      })
      // 异步加载该基金的持仓和待确认信息
      this._loadFundSummary(fund.code)
    }
  },

  async _loadFundSummary(code) {
    try {
      const [holdings, pendingTxns, accounts] = await Promise.all([
        listHoldings(),
        listTransactions({ status: 'pending', limit: 200 }),
        listAccounts(),
      ])
      let holding = holdings.find(h => h.fund_code === code)

      // 防御：若持仓表无记录，从基金账户的 balance 回退
      const acct = accounts.find(a => a.account_type === 'fund' && a.fund_code === code)
      const acctBalance = acct ? (acct.balance || 0) : 0
      const acctPending = acct ? (acct.pending_amount || 0) : 0

      if (!holding && acct && acctBalance > 0) {
        holding = {
          fund_code: code,
          total_cost: acctBalance,
          current_value: acctBalance,
          total_shares: 0,
          daily_profit: 0,
          profit_rate: 0,
        }
      }

      const pendingTotal = pendingTxns
        .filter(t => t.fund_code === code)
        .reduce((sum, t) => sum + (t.amount || 0), acctPending)

      const profit = holding ? (holding.daily_profit || 0) : 0
      const hasHold = !!holding || (acct && acctBalance > 0)
      this.setData({
        fundSummary: {
          totalCost: holding ? this._fmt(holding.total_cost) : null,
          currentValue: holding ? this._fmt(holding.current_value) : null,
          totalShares: holding ? Number(holding.total_shares || 0).toFixed(2) : null,
          dailyProfit: holding ? this._fmt(holding.daily_profit) : null,
          profitRate: holding ? Number(holding.profit_rate || 0).toFixed(2) : null,
          profitClass: profit >= 0 ? 'amount-up' : 'amount-down',
          pendingAmt: pendingTotal > 0 ? this._fmt(pendingTotal) : null,
          hasHold,
          hasPending: pendingTotal > 0,
        },
      })
    } catch (e) {
      console.error('加载基金摘要失败:', e)
    }
  },

  onAccountPickerChange(e) {
    const idx = e.detail.value
    const account = this.data.accounts[idx]
    if (account) {
      this.setData({
        'form.from_account_id': account.id,
        selectedAccountDisplay: account.label + ' (¥' + this._fmt(account.balance) + ')',
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

  async onSubmit() {
    const { form, editId } = this.data
    if (!form.fund_code || !form.from_account_id || !form.amount) {
      wx.showToast({ title: '请完善必填项', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      const freqLabel = this.data.freqOptions.find(o => o.value === form.frequency)?.label || form.frequency
      const planName = form.fund_code + '-' + freqLabel

      const payload = {
        plan_name: planName,
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

  _fmt(v) {
    if (v == null || (typeof v === 'number' && isNaN(v))) return '0.00'
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  _fmtDate(d) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  },
})
