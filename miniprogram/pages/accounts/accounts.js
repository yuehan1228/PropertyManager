import { listAccounts, createAccount, updateAccount, deleteAccount } from '../../services/api'

Page({
  data: {
    accounts: [],
    loading: true,
    showForm: false,
    editingAccount: null,
    form: { label: '', bank_name: '', balance: 0, remark: '' },
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const accounts = await listAccounts()
      this.setData({ accounts, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  // 表单
  onAdd() {
    this.setData({
      showForm: true,
      editingAccount: null,
      form: { label: '', bank_name: '', balance: 0, remark: '' },
    })
  },
  onEdit(e) {
    const id = e.detail.id
    const acct = this.data.accounts.find(a => a.id === id)
    if (!acct) return
    this.setData({
      showForm: true,
      editingAccount: acct,
      form: {
        label: acct.label,
        bank_name: acct.bank_name || '',
        balance: acct.balance,
        remark: acct.remark || '',
      },
    })
  },
  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },
  async onFormSubmit() {
    const { form, editingAccount } = this.data
    if (!form.label.trim()) {
      wx.showToast({ title: '请输入账户标识', icon: 'none' })
      return
    }
    try {
      if (editingAccount) {
        await updateAccount(editingAccount.id, {
          label: form.label,
          bank_name: form.bank_name,
          balance: parseFloat(form.balance) || 0,
          remark: form.remark,
        })
      } else {
        await createAccount({
          label: form.label,
          bank_name: form.bank_name,
          balance: parseFloat(form.balance) || 0,
          remark: form.remark,
        })
      }
      this.setData({ showForm: false })
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.loadData()
    } catch (e) {
      // handled in api
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
    } catch (e) {
      // handled
    }
  },

  onCloseForm() {
    this.setData({ showForm: false })
  },

  _showConfirm(msg) {
    return new Promise(resolve => {
      wx.showModal({ title: '确认', content: msg, success: r => resolve(r.confirm) })
    })
  },
})
