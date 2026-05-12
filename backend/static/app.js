/**
 * 个人资产追踪系统 — Web 前端 SPA
 * 纯 vanilla JS，无框架依赖
 */
const API = '/api'

// =========================================================================
// 工具函数
// =========================================================================
const $ = (sel, ctx = document) => ctx.querySelector(sel)
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)]
const fmt = (v, d = 2) => {
  if (v == null || isNaN(v)) return '--'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}
const fmtPct = (v) => {
  if (v == null || isNaN(v)) return '--'
  return (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%'
}
const sign = (v) => v >= 0 ? '+' : ''
const dateStr = (d) => {
  if (!d) return ''
  const dt = new Date(d)
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
const now = () => {
  const d = new Date()
  return dateStr(d)
}
const h = (tag, attrs = {}, ...children) => {
  const el = document.createElement(tag)
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class' || k === 'className') el.className = v
    else if (k === 'onClick') el.addEventListener('click', v)
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v)
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v)
    else if (k === 'html') el.innerHTML = v
    else el.setAttribute(k, v)
  }
  for (const child of children) {
    if (typeof child === 'string') el.appendChild(document.createTextNode(child))
    else if (child instanceof Node) el.appendChild(child)
  }
  return el
}

// =========================================================================
// API 层
// =========================================================================
async function api(path, opts = {}) {
  const { method = 'GET', body } = opts
  const headers = { 'Content-Type': 'application/json' }
  const res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

// =========================================================================
// Toast
// =========================================================================
function toast(msg, type = '') {
  const el = h('div', { class: 'toast ' + (type ? 'toast-' + type : '') }, msg)
  document.body.appendChild(el)
  setTimeout(() => { el.remove() }, 2200)
}

// =========================================================================
// 状态
// =========================================================================
const state = {
  page: 'dashboard', // dashboard | funds | plans | accounts | transactions
  dashboard: null,
  funds: [],
  accounts: [],
  holdings: [],
  plans: [],
  transactions: [],
  planFilter: 'active',
  txnFilter: {},
  modal: null, // { type, data }
}

// =========================================================================
// 页面路由
// =========================================================================
function setPage(name) {
  state.page = name
  $$('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.page === name))
  render()
}

function render() {
  const app = $('#app')
  app.innerHTML = ''
  switch (state.page) {
    case 'dashboard': renderDashboard(app); break
    case 'funds': renderFunds(app); break
    case 'plans': renderPlans(app); break
    case 'accounts': renderAccounts(app); break
    case 'transactions': renderTransactions(app); break
  }
  if (state.modal) renderModal()
}

// =========================================================================
// 总览看板
// =========================================================================
async function loadDashboard() {
  try {
    state.dashboard = await api('/dashboard')
  } catch (e) {
    toast(e.message, 'error')
  }
}

function renderDashboard(app) {
  const d = state.dashboard
  if (!d) {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '📊'),
      h('div', { class: 'empty-state-message' }, '加载中...'),
    ))
    return
  }

  // Hero card
  app.appendChild(
    h('div', { class: 'hero-card' },
      h('div', { class: 'hero-label' }, '总资产 (CNY)'),
      h('div', { class: 'hero-amount' }, fmt(d.total_assets, 0)),
      h('div', { class: 'hero-sub' },
        h('div', { class: 'hero-sub-item' },
          h('span', { class: 'hero-sub-label' }, '日收益'),
          h('span', { class: 'hero-sub-value ' + (d.daily_profit >= 0 ? 'up' : 'down') },
            sign(d.daily_profit) + fmt(d.daily_profit)),
        ),
        h('div', { class: 'hero-sub-item text-right' },
          h('span', { class: 'hero-sub-label' }, '累计盈亏'),
          h('span', { class: 'hero-sub-value ' + (d.cumulative_profit >= 0 ? 'up' : 'down') },
            sign(d.cumulative_profit) + fmt(d.cumulative_profit)),
        ),
      ),
      h('div', { class: 'hero-split' },
        h('div', { class: 'hero-split-item', onClick: () => setPage('accounts') },
          h('span', { class: 'hero-split-label' }, '💰 储蓄卡'),
          h('span', { class: 'hero-split-value' }, fmt(d.total_savings)),
        ),
        h('div', { class: 'hero-split-item text-right', onClick: () => setPage('funds') },
          h('span', { class: 'hero-split-label' }, '📈 基金市值'),
          h('span', { class: 'hero-split-value' }, fmt(d.total_fund_value)),
        ),
      ),
      h('div', { class: 'refresh-time' }, '点击标签栏刷新'),
    )
  )

  // Actions
  app.appendChild(
    h('div', { class: 'actions-row' },
      h('button', { class: 'btn btn-outline', onClick: () => setPage('transactions') }, '📋 交易记录'),
      h('button', { class: 'btn btn-outline', onClick: () => setPage('accounts') }, '💳 管理账户'),
      h('button', { class: 'btn btn-outline', onClick: () => setPage('funds') }, '🔍 基金列表'),
    )
  )

  // Holdings
  app.appendChild(h('div', { class: 'section-title' }, '持仓概况'))
  if (d.holdings && d.holdings.length > 0) {
    const list = h('div', { class: 'card' })
    d.holdings.forEach(hd => {
      list.appendChild(
        h('div', { class: 'list-row', onClick: () => setPage('funds') },
          h('div', { class: 'list-row-left' },
            h('span', { class: 'list-row-icon' }, '📈'),
            h('div', {},
              h('div', { class: 'list-row-title' }, hd.fund_name || hd.fund_code),
              h('div', { class: 'list-row-sub' }, '份额 ' + fmt(hd.total_shares)),
            ),
          ),
          h('div', { class: 'text-right' },
            h('div', { class: 'list-row-value' }, fmt(hd.current_value)),
            h('div', { class: 'list-row-change ' + (hd.daily_profit >= 0 ? 'up' : 'down') },
              sign(hd.daily_profit) + fmt(hd.daily_profit)),
          ),
        )
      )
    })
    app.appendChild(list)
  } else {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '📭'),
      h('div', { class: 'empty-state-message' }, '暂无持仓'),
      h('div', { class: 'empty-state-tip' }, '添加基金并买入吧'),
    ))
  }

  // Chart placeholder
  app.appendChild(h('div', { class: 'section-title' }, '资产趋势'))
  app.appendChild(h('div', { class: 'card chart-placeholder' }, '每日快照自动记录中'))
}

// =========================================================================
// 基金列表
// =========================================================================
async function loadFunds() {
  try {
    state.funds = await api('/funds?is_active=1')
  } catch (e) { toast(e.message, 'error') }
}

function renderFunds(app) {
  app.appendChild(
    h('div', { class: 'page-header' },
      h('div', { class: 'page-title' }, '基金列表'),
      h('button', { class: 'btn btn-primary btn-sm', onClick: () => openModal('addFund') }, '+ 添加基金'),
    )
  )

  if (state.funds.length === 0) {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '🔍'),
      h('div', { class: 'empty-state-message' }, '暂无基金'),
      h('div', { class: 'empty-state-tip' }, '点击上方按钮添加第一只基金'),
    ))
    return
  }

  const list = h('div', {})
  state.funds.forEach(f => {
    list.appendChild(
      h('div', { class: 'card', style: { cursor: 'pointer' }, onClick: () => openModal('fundDetail', f) },
        h('div', { class: 'flex justify-between items-center' },
          h('div', { class: 'flex-1' },
            h('div', { style: 'font-size:15px;font-weight:600' }, f.name || f.code),
            h('div', { style: 'font-size:12px;color:#9ca3af;margin-top:2px' }, f.code),
          ),
          h('div', { class: 'text-right' },
            h('div', { style: 'font-size:18px;font-weight:700' }, f.nav ? f.nav.toFixed(4) : '--'),
            h('div', { class: f.daily_change >= 0 ? 'up' : 'down', style: 'font-size:12px;margin-top:2px' },
              fmtPct(f.daily_change)),
          ),
        ),
        h('div', { class: 'flex gap-sm mt-sm', style: 'font-size:12px;color:#6b7280' },
          h('span', {}, '类型: ' + (f.fund_type || '--')),
          h('span', {}, '确认: ' + f.settle_cycle),
          h('span', {}, '赎回: ' + f.redeem_cycle),
        ),
      )
    )
  })
  app.appendChild(list)
}

// =========================================================================
// 定投计划
// =========================================================================
async function loadPlans() {
  try {
    const q = state.planFilter === 'active' ? '?status=active' : ''
    state.plans = await api('/plans' + q)
  } catch (e) { toast(e.message, 'error') }
}

function renderPlans(app) {
  app.appendChild(
    h('div', { class: 'page-header' },
      h('div', { class: 'page-title' }, '定投计划'),
      h('button', { class: 'btn btn-primary btn-sm', onClick: () => openModal('planForm') }, '+ 新建计划'),
    )
  )

  // Sub tabs
  app.appendChild(
    h('div', { class: 'sub-tabs' },
      h('button', {
        class: 'sub-tab ' + (state.planFilter === 'active' ? 'active' : ''),
        onClick() { state.planFilter = 'active'; loadPlans().then(render) },
      }, '进行中'),
      h('button', {
        class: 'sub-tab ' + (state.planFilter === 'all' ? 'active' : ''),
        onClick() { state.planFilter = 'all'; loadPlans().then(render) },
      }, '全部'),
    )
  )

  if (state.plans.length === 0) {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '📅'),
      h('div', { class: 'empty-state-message' }, '暂无定投计划'),
      h('div', { class: 'empty-state-tip' }, '创建自动定投，省心省力'),
    ))
    return
  }

  const list = h('div', {})
  state.plans.forEach(p => {
    const freqMap = { daily: '日', weekly: '周', biweekly: '双周', monthly: '月' }
    const statusMap = { active: ['运行中', 'tag-green'], paused: ['已暂停', 'tag-gray'], stopped: ['已停止', 'tag-gray'] }
    const [sLabel, sTag] = statusMap[p.status] || [p.status, 'tag-gray']

    list.appendChild(
      h('div', { class: 'card plan-card' },
        h('div', { class: 'flex justify-between items-center' },
          h('div', { class: 'flex-1' },
            h('div', { class: 'plan-name' }, p.plan_name),
            h('div', { class: 'plan-meta' },
              h('span', { class: 'tag tag-blue' }, p.fund_code),
              h('span', { style: 'font-size:13px;color:#6b7280' }, '¥' + fmt(p.amount) + ' / ' + freqMap[p.frequency]),
            ),
          ),
          h('span', { class: 'tag ' + sTag }, sLabel),
        ),
        h('div', { class: 'divider' }),
        h('div', { class: 'flex justify-between items-center' },
          h('div', { class: 'plan-progress' },
            '已完成 ' + p.completed_rounds + (p.total_rounds ? '/' + p.total_rounds : '') + ' 期'),
          h('div', { class: 'flex gap-xs' },
            h('button', { class: 'btn btn-outline btn-sm', onClick: () => openModal('planForm', p) }, '编辑'),
            h('button', {
              class: 'btn btn-outline btn-sm',
              async onClick() {
                const ns = p.status === 'active' ? 'paused' : 'active'
                try { await api('/plans/' + p.id, { method: 'PUT', body: { status: ns } }); toast('已' + (ns === 'active' ? '启用' : '暂停'), 'success'); loadPlans().then(render) } catch (e) { toast(e.message, 'error') }
              },
            }, p.status === 'active' ? '暂停' : '启用'),
            h('button', {
              class: 'btn btn-ghost btn-sm btn-danger',
              async onClick() {
                if (!confirm('确定删除此定投计划？')) return
                try { await api('/plans/' + p.id, { method: 'DELETE' }); toast('已删除', 'success'); loadPlans().then(render) } catch (e) { toast(e.message, 'error') }
              },
            }, '删除'),
          ),
        ),
        p.next_execute_date && p.status === 'active'
          ? h('div', { class: 'plan-next' }, '下次执行: ' + p.next_execute_date)
          : null,
      )
    )
  })
  app.appendChild(list)
}

// =========================================================================
// 账户管理
// =========================================================================
async function loadAccounts() {
  try {
    state.accounts = await api('/accounts')
  } catch (e) { toast(e.message, 'error') }
}

function renderAccounts(app) {
  app.appendChild(
    h('div', { class: 'page-header' },
      h('div', { class: 'page-title' }, '账户管理'),
      h('button', { class: 'btn btn-primary btn-sm', onClick: () => openModal('accountForm') }, '+ 添加账户'),
    )
  )

  if (state.accounts.length === 0) {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '💳'),
      h('div', { class: 'empty-state-message' }, '暂无账户'),
      h('div', { class: 'empty-state-tip' }, '添加储蓄卡开始追踪资产'),
    ))
    return
  }

  const list = h('div', {})
  state.accounts.forEach(a => {
    list.appendChild(
      h('div', { class: 'card list-row', onClick: () => openModal('accountForm', a) },
        h('div', { class: 'list-row-left' },
          h('span', { class: 'list-row-icon' }, '💳'),
          h('div', {},
            h('div', { class: 'list-row-title' }, a.label),
            a.bank_name ? h('div', { class: 'list-row-sub' }, a.bank_name) : null,
          ),
        ),
        h('div', { class: 'text-right' },
          h('div', { class: 'list-row-value' }, fmt(a.balance)),
          h('div', { class: 'list-row-sub' }, a.currency),
        ),
      )
    )
  })
  app.appendChild(list)
}

// =========================================================================
// 交易记录
// =========================================================================
async function loadTransactions() {
  try {
    const params = new URLSearchParams()
    if (state.txnFilter.fund_code) params.set('fund_code', state.txnFilter.fund_code)
    if (state.txnFilter.status) params.set('status', state.txnFilter.status)
    params.set('limit', '50')
    state.transactions = await api('/transactions?' + params.toString())
  } catch (e) { toast(e.message, 'error') }
}

function renderTransactions(app) {
  app.appendChild(
    h('div', { class: 'page-header' },
      h('div', { class: 'page-title' }, '交易记录'),
    )
  )

  if (state.transactions.length === 0) {
    app.appendChild(h('div', { class: 'empty-state' },
      h('div', { class: 'empty-state-icon' }, '📋'),
      h('div', { class: 'empty-state-message' }, '暂无交易记录'),
    ))
    return
  }

  const typeMap = { buy: '买入', sell: '卖出', auto_buy: '定投买入', dividend: '分红' }
  const statusMap = { pending: ['待确认', 'tag-yellow'], confirmed: ['已确认', 'tag-blue'], settled: ['已到账', 'tag-green'] }

  const list = h('div', {})
  state.transactions.forEach(t => {
    const [sLabel, sTag] = statusMap[t.status] || [t.status, 'tag-gray']
    list.appendChild(
      h('div', { class: 'card txn-card' },
        h('div', { class: 'flex justify-between items-center' },
          h('div', { class: 'flex-1' },
            h('div', { class: 'txn-name' }, t.fund_name || t.fund_code),
            h('div', { class: 'txn-type' }, (typeMap[t.trans_type] || t.trans_type) + ' · ' + t.order_date),
          ),
          h('div', { class: 'text-right' },
            h('div', { class: 'txn-amount' }, '¥' + fmt(t.amount)),
            t.shares ? h('div', { class: 'txn-shares' }, t.shares.toFixed(2) + ' 份') : null,
          ),
        ),
        h('div', { class: 'txn-status-row' },
          h('span', { class: 'tag ' + sTag }, sLabel),
          t.confirm_date ? h('span', { class: 'txn-meta' }, '确认: ' + t.confirm_date) : null,
          t.status === 'pending'
            ? h('button', {
              class: 'btn btn-ghost btn-sm btn-danger', style: { marginLeft: 'auto' },
              async onClick() {
                if (!confirm('确定删除此交易？')) return
                try { await api('/transactions/' + t.id, { method: 'DELETE' }); toast('已删除', 'success'); loadTransactions().then(render) } catch (e) { toast(e.message, 'error') }
              },
            }, '删除')
            : null,
        ),
      )
    )
  })
  app.appendChild(list)
}

// =========================================================================
// Modal 管理
// =========================================================================
function openModal(type, data = null) {
  state.modal = { type, data }
  render()
}

function closeModal() {
  state.modal = null
  render()
}

function renderModal() {
  const m = state.modal
  if (!m) return

  const overlay = h('div', { class: 'modal-overlay', onClick: (e) => { if (e.target === overlay) closeModal() } })
  let content

  switch (m.type) {
    case 'addFund': content = renderModalAddFund(); break
    case 'fundDetail': content = renderModalFundDetail(m.data); break
    case 'accountForm': content = renderModalAccountForm(m.data); break
    case 'planForm': content = renderModalPlanForm(m.data); break
  }

  overlay.appendChild(h('div', { class: 'modal-content' }, content))
  document.body.appendChild(overlay)
}

// -- 添加基金 --
function renderModalAddFund() {
  const container = document.createDocumentFragment()
  container.appendChild(h('div', { class: 'modal-title' }, '添加基金'))

  let codeInput
  const form = h('div', {},
    h('div', { class: 'form-group' },
      h('label', { class: 'form-label' }, '基金代码 (6位)'),
      codeInput = h('input', { class: 'form-input', type: 'text', maxlength: '6', placeholder: '如：000001', style: 'font-size:28px;text-align:center;letter-spacing:8px;font-weight:700' }),
    ),
    h('div', { class: 'text-center mt-sm' },
      h('span', { style: 'font-size:12px;color:#9ca3af' }, '输入基金代码后将自动拉取基金信息'),
    ),
    h('div', { class: 'flex gap-sm mt-md' },
      h('button', { class: 'btn btn-outline flex-1', onClick: closeModal }, '取消'),
      h('button', {
        class: 'btn btn-primary flex-1',
        async onClick() {
          const code = codeInput.value.trim()
          if (code.length !== 6) { toast('请输入6位基金代码', 'error'); return }
          try {
            await api('/funds', { method: 'POST', body: { code } })
            toast('添加成功，正在同步数据...', 'success')
            closeModal()
            loadFunds().then(render)
          } catch (e) { toast(e.message, 'error') }
        },
      }, '确认添加'),
    ),
  )
  container.appendChild(form)
  return container
}

// -- 基金详情 --
function renderModalFundDetail(f) {
  const container = document.createDocumentFragment()
  container.appendChild(h('div', { class: 'modal-title' }, f.name || f.code))

  container.appendChild(
    h('div', { class: 'card', style: 'margin:0' },
      h('div', { class: 'flex justify-between items-center' },
        h('div', {},
          h('div', { style: 'font-size:15px;font-weight:600' }, f.code),
          h('div', { style: 'font-size:12px;color:#9ca3af;margin-top:2px' }, f.name || ''),
        ),
        h('div', { class: 'text-right' },
          h('div', { style: 'font-size:26px;font-weight:700' }, f.nav ? f.nav.toFixed(4) : '--'),
          h('div', { class: f.daily_change >= 0 ? 'up' : 'down', style: 'font-size:13px' }, fmtPct(f.daily_change)),
        ),
      ),
      h('div', { class: 'divider' }),
      h('div', { class: 'detail-grid' },
        h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '类型'), h('div', { class: 'detail-value' }, f.fund_type || '--')),
        h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '确认周期'), h('div', { class: 'detail-value' }, f.settle_cycle)),
        h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '赎回到账'), h('div', { class: 'detail-value' }, f.redeem_cycle)),
        f.acc_nav ? h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '累计净值'), h('div', { class: 'detail-value' }, f.acc_nav.toFixed(4))) : null,
        h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '净值日期'), h('div', { class: 'detail-value' }, f.nav_date || '--')),
        f.estimate_nav ? h('div', { class: 'detail-item' }, h('span', { class: 'detail-label' }, '盘中估值'), h('div', { class: 'detail-value' }, f.estimate_nav.toFixed(4))) : null,
      ),
    )
  )

  container.appendChild(
    h('div', { class: 'flex gap-sm mt-md' },
      h('button', {
        class: 'btn btn-primary flex-1',
        async onClick() {
          try { await api('/funds/' + f.code + '/sync', { method: 'POST' }); toast('同步成功', 'success'); closeModal(); loadFunds().then(render) } catch (e) { toast(e.message, 'error') }
        },
      }, '🔄 同步数据'),
      h('button', { class: 'btn btn-outline flex-1', onClick: closeModal }, '关闭'),
    )
  )
  return container
}

// -- 账户表单 --
function renderModalAccountForm(data) {
  const isEdit = !!data
  const container = document.createDocumentFragment()
  container.appendChild(h('div', { class: 'modal-title' }, isEdit ? '编辑账户' : '添加账户'))

  const fields = {
    label: data?.label || '',
    bank_name: data?.bank_name || '',
    balance: data?.balance ?? '',
    remark: data?.remark || '',
  }
  const inputs = {}
  const form = h('div', {}
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '标识 *'), inputs.label = h('input', { class: 'form-input', value: fields.label, placeholder: '如：招行工资卡' }))
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '银行名称'), inputs.bank = h('input', { class: 'form-input', value: fields.bank_name, placeholder: '如：招商银行' }))
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '当前余额'), inputs.balance = h('input', { class: 'form-input', type: 'number', value: fields.balance, placeholder: '0.00' }))
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '备注'), inputs.remark = h('input', { class: 'form-input', value: fields.remark, placeholder: '可选' }))
    , h('div', { class: 'flex gap-sm mt-md' },
      h('button', { class: 'btn btn-outline flex-1', onClick: closeModal }, '取消'),
      h('button', {
        class: 'btn btn-primary flex-1',
        async onClick() {
          const body = {
            label: inputs.label.value.trim(),
            bank_name: inputs.bank.value.trim() || null,
            balance: parseFloat(inputs.balance.value) || 0,
            remark: inputs.remark.value.trim() || null,
          }
          if (!body.label) { toast('请输入账户标识', 'error'); return }
          try {
            if (isEdit) {
              await api('/accounts/' + data.id, { method: 'PUT', body })
            } else {
              await api('/accounts', { method: 'POST', body })
            }
            toast('保存成功', 'success')
            closeModal()
            loadAccounts().then(render)
            loadDashboard().then(render)
          } catch (e) { toast(e.message, 'error') }
        },
      }, '保存'),
    ),
  )
  if (isEdit) {
    form.appendChild(
      h('div', { class: 'text-center mt-sm' },
        h('button', {
          class: 'btn btn-ghost btn-sm btn-danger',
          async onClick() {
            if (!confirm('确定删除此账户？')) return
            try { await api('/accounts/' + data.id, { method: 'DELETE' }); toast('已删除', 'success'); closeModal(); loadAccounts().then(render) } catch (e) { toast(e.message, 'error') }
          },
        }, '删除账户'),
      )
    )
  }
  container.appendChild(form)
  return container
}

// -- 定投表单 --
function renderModalPlanForm(data) {
  const isEdit = !!data
  const container = document.createDocumentFragment()
  container.appendChild(h('div', { class: 'modal-title' }, isEdit ? '编辑定投计划' : '新建定投计划'))

  const fields = {
    plan_name: data?.plan_name || '',
    fund_code: data?.fund_code || '',
    from_account_id: data?.from_account_id || '',
    amount: data?.amount || '',
    frequency: data?.frequency || 'monthly',
    execute_day: data?.execute_day || 1,
    total_rounds: data?.total_rounds || '',
    start_date: data?.start_date || now(),
  }
  const inputs = {}

  const form = h('div', {}
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '计划名称 *'), inputs.plan_name = h('input', { class: 'form-input', value: fields.plan_name, placeholder: '如：每月工资定投' }))
    , h('div', { class: 'form-group' },
      h('label', { class: 'form-label' }, '目标基金 *'),
      inputs.fund_code = h('select', { class: 'form-select' },
        h('option', { value: '' }, '请选择基金'),
        ...state.funds.map(f => h('option', { value: f.code, selected: f.code === fields.fund_code ? 'selected' : undefined }, f.code + ' ' + (f.name || '')))
      ),
    )
    , h('div', { class: 'form-group' },
      h('label', { class: 'form-label' }, '扣款账户 *'),
      inputs.from_account_id = h('select', { class: 'form-select' },
        h('option', { value: '' }, '请选择账户'),
        ...state.accounts.map(a => h('option', { value: String(a.id), selected: String(a.id) === String(fields.from_account_id) ? 'selected' : undefined }, a.label + ' (' + fmt(a.balance) + ')'))
      ),
    )
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '每次金额 *'), inputs.amount = h('input', { class: 'form-input', type: 'number', value: fields.amount, placeholder: '0.00' }))
    , h('div', { class: 'form-group' },
      h('label', { class: 'form-label' }, '扣款频率'),
      inputs.frequency = h('select', { class: 'form-select' },
        h('option', { value: 'monthly', selected: fields.frequency === 'monthly' ? 'selected' : undefined }, '每月'),
        h('option', { value: 'biweekly', selected: fields.frequency === 'biweekly' ? 'selected' : undefined }, '每两周'),
        h('option', { value: 'weekly', selected: fields.frequency === 'weekly' ? 'selected' : undefined }, '每周'),
        h('option', { value: 'daily', selected: fields.frequency === 'daily' ? 'selected' : undefined }, '每日'),
      ),
    )
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '每月执行日'), inputs.execute_day = h('select', { class: 'form-select' },
      ...[1, 5, 10, 15, 20, 25, 28].map(d => h('option', { value: String(d), selected: d === fields.execute_day ? 'selected' : undefined }, d + ' 日'))
    ))
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '开始日期'), inputs.start_date = h('input', { class: 'form-input', type: 'date', value: fields.start_date }))
    , h('div', { class: 'form-group' }, h('label', { class: 'form-label' }, '总期数（留空无限）'), inputs.total_rounds = h('input', { class: 'form-input', type: 'number', value: fields.total_rounds, placeholder: '如：12' }))
    , h('div', { class: 'flex gap-sm mt-md' },
      h('button', { class: 'btn btn-outline flex-1', onClick: closeModal }, '取消'),
      h('button', {
        class: 'btn btn-primary flex-1',
        async onClick() {
          const body = {
            plan_name: inputs.plan_name.value.trim(),
            fund_code: inputs.fund_code.value,
            from_account_id: Number(inputs.from_account_id.value),
            amount: parseFloat(inputs.amount.value),
            frequency: inputs.frequency.value,
            execute_day: Number(inputs.execute_day.value),
            total_rounds: inputs.total_rounds.value ? Number(inputs.total_rounds.value) : null,
            start_date: inputs.start_date.value,
          }
          if (!body.plan_name || !body.fund_code || !body.from_account_id || !body.amount) {
            toast('请完善必填项', 'error'); return
          }
          try {
            if (isEdit) {
              await api('/plans/' + data.id, { method: 'PUT', body })
            } else {
              await api('/plans', { method: 'POST', body })
            }
            toast('保存成功', 'success')
            closeModal()
            loadPlans().then(render)
          } catch (e) { toast(e.message, 'error') }
        },
      }, '保存'),
    ),
  )
  container.appendChild(form)
  return container
}

// =========================================================================
// 初始化
// =========================================================================
async function init() {
  // Tab 事件
  $$('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => setPage(tab.dataset.page))
  })

  // 初始加载
  await Promise.all([
    loadDashboard(),
    loadFunds(),
    loadAccounts(),
    loadPlans(),
    loadTransactions(),
  ])
  render()

  // 每 60 秒自动刷新看板
  setInterval(async () => {
    await loadDashboard()
    if (state.page === 'dashboard') render()
  }, 60000)
}

document.addEventListener('DOMContentLoaded', init)
