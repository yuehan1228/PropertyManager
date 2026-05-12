import { addFund, syncFund } from '../../services/api'

Page({
  data: {
    code: '',
    submitting: false,
  },

  onCodeInput(e) {
    this.setData({ code: e.detail.value.replace(/\D/g, '').slice(0, 6) })
  },

  async onSubmit() {
    const code = this.data.code.trim()
    if (code.length !== 6) {
      wx.showToast({ title: '请输入6位基金代码', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      await addFund({ code })
      wx.showToast({ title: '添加成功，正在同步数据...', icon: 'success' })
      // 回到列表
      setTimeout(() => {
        wx.navigateBack()
      }, 1200)
    } catch (e) {
      this.setData({ submitting: false })
    }
  },
})
