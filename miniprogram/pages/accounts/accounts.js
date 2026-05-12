import { listAccounts, listFunds, createAccount, updateAccount, deleteAccount } from '../../services/api'

Page({
  data: {
    accounts: [],
    funds: [],
    loading: true,
    showForm: false,
    editingAccount: null,
    form: {
      account_type: 'bank',
      label: '',
      bank_name: '',
      balance: '',
      fund_code: '',
      remark: '',
    },
    selectedFundDisplay: '请选择基金',
    submitting: false,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const [accounts, funds] = await Promise.all([
        listAccounts(),
        listFunds(1),
      ])
      const list = (accounts || []).map(item => ({
        ...item,
        _balance: this._fmt(item.balance),
        _pending: item.account_type === 'fund' ? this._fmt(item.pending_amount || 0) : null,
        _icon: item.account_type === 'fund' ? '📈' : '💳',
        _typeLabel: item.account_type === 'fund' ? '基金' : '银行卡',
      }))
      this.setData({ accounts: list, funds, loading: false })
    } catch (e) {
      console.error('加载账户失败:', e)
      this.setData({ loading: false })
    }
  },

  onAdd() {
    this.setData({
      showForm: true,
      editingAccount: null,
      selectedFundDisplay: '请选择基金',
      form: { account_type: 'bank', label: '', bank_name: '', balance: '', pending_amount: '', fund_code: '', remark: '' },
    })
  },

  onEdit(e) {
    const id = e.detail.id
    const acct = this.data.accounts.find(a => a.id === id)
    if (!acct) return
    this.setData({
      showForm: true,
      editingAccount: acct,
      selectedFundDisplay: acct.fund_code ? acct.fund_code + ' ' + (acct.bank_name || '') : '请选择基金',
      form: {
        account_type: acct.account_type || 'bank',
        label: acct.label,
        bank_name: acct.bank_name || '',
        balance: String(acct.balance || ''),
        pending_amount: String(acct.pending_amount || ''),
        fund_code: acct.fund_code || '',
        remark: acct.remark || '',
      },
    })
  },

  onTypeChange(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      'form.account_type': type,
      selectedFundDisplay: '请选择基金',
      'form.fund_code': '',
    })
  },

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

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  async onFormSubmit() {
    const { form, editingAccount } = this.data
    if (!form.label.trim()) {
      wx.showToast({ title: '请输入账户名称', icon: 'none' })
      return
    }
    if (form.account_type === 'fund' && !form.fund_code) {
      wx.showToast({ title: '请选择基金', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      const payload = {
        account_type: form.account_type,
        label: form.label,
        bank_name: form.bank_name,
        balance: parseFloat(form.balance) || 0,
        pending_amount: parseFloat(form.pending_amount) || 0,
        fund_code: form.account_type === 'fund' ? form.fund_code : null,
        remark: form.remark,
      }
      if (editingAccount) {
        await updateAccount(editingAccount.id, payload)
      } else {
        await createAccount(payload)
      }
      this.setData({ showForm: false })
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.loadData()
    } catch (e) {
      this.setData({ submitting: false })
    }
  },

  async onDelete() {
    const { editingAccount } = this.data
    if (!editingAccount) return
    const confirm = await this._showConfirm('确定删除此账户？')
    if (!confirm) return
    try {
      await deleteAccount(editingAccount.id)
      this.setData({ showForm: false })
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadData()
    } catch (e) { /* handled */ }
  },

  onCloseForm() {
    this.setData({ showForm: false })
  },

  noop() {},

  _fmt(v) {
    if (v == null || (typeof v === 'number' && isNaN(v))) return '0.00'
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  },
  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
