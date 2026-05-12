Component({
  properties: {
    code: { type: String, value: '' },
    name: { type: String, value: '' },
    icon: { type: String, value: '📈' },
    navText: { type: String, value: '--' },
    changeText: { type: String, value: '0.00%' },
    changeClass: { type: String, value: 'amount-up' },
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { code: this.properties.code })
    },
  },
})
