Component({
  properties: {
    id: { type: Number, value: 0 },
    label: { type: String, value: '' },
    bank: { type: String, value: '' },
    balanceText: { type: String, value: '0.00' },
    pendingText: { type: String, value: '' },
    currency: { type: String, value: 'CNY' },
    icon: { type: String, value: '💳' },
    typeLabel: { type: String, value: '银行卡' },
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.properties.id })
    },
  },
})
