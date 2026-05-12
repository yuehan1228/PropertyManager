Component({
  properties: {
    id: { type: Number, value: 0 },
    label: { type: String, value: '' },
    bank: { type: String, value: '' },
    balance: { type: Number, value: 0 },
    currency: { type: String, value: 'CNY' },
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.properties.id })
    },
    fmt(v) {
      if (v == null) return '0.00'
      return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
  },
})
