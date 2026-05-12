Component({
  properties: {
    code: { type: String, value: '' },
    name: { type: String, value: '' },
    nav: { type: Number, value: 0 },
    change: { type: Number, value: 0 },
    icon: { type: String, value: '📈' },
    navText: { type: String, value: '' },
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { code: this.properties.code })
    },
    fmt(v) {
      if (v == null) return '--'
      return Number(v).toFixed(2)
    },
  },
})
