/** API 服务层 —— 封装后端所有接口 */
const app = getApp()

function baseUrl() {
  return app.globalData.baseUrl
}

function request(path, options = {}) {
  const { method = 'GET', data, silent = false } = options
  return new Promise((resolve, reject) => {
    if (!silent) wx.showLoading({ title: '加载中...', mask: true })
    wx.request({
      url: baseUrl() + path,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          const msg = res.data?.detail || res.data?.message || '请求失败'
          if (!silent) wx.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
        }
      },
      fail(err) {
        if (!silent) wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
      complete() {
        if (!silent) wx.hideLoading()
      },
    })
  })
}

// ----------------------------------------------------------------
// Dashboard
// ----------------------------------------------------------------
export function getDashboard() {
  return request('/api/dashboard')
}

export function getSnapshots(limit = 30) {
  return request(`/api/dashboard/snapshots?limit=${limit}`)
}

// ----------------------------------------------------------------
// 账户
// ----------------------------------------------------------------
export function listAccounts() {
  return request('/api/accounts')
}

export function createAccount(data) {
  return request('/api/accounts', { method: 'POST', data })
}

export function updateAccount(id, data) {
  return request(`/api/accounts/${id}`, { method: 'PUT', data })
}

export function deleteAccount(id) {
  return request(`/api/accounts/${id}`, { method: 'DELETE' })
}

// ----------------------------------------------------------------
// 基金
// ----------------------------------------------------------------
export function listFunds(isActive) {
  const q = isActive !== undefined ? `?is_active=${isActive}` : ''
  return request('/api/funds' + q)
}

export function getFund(code) {
  return request(`/api/funds/${code}`)
}

export function addFund(data) {
  return request('/api/funds', { method: 'POST', data })
}

export function updateFund(code, data) {
  return request(`/api/funds/${code}`, { method: 'PUT', data })
}

export function syncFund(code) {
  return request(`/api/funds/${code}/sync`, { method: 'POST' })
}

export function getNavHistory(code, limit = 30) {
  return request(`/api/funds/${code}/nav-history?limit=${limit}`)
}

// ----------------------------------------------------------------
// 持仓
// ----------------------------------------------------------------
export function listHoldings() {
  return request('/api/holdings')
}

// ----------------------------------------------------------------
// 交易
// ----------------------------------------------------------------
export function listTransactions(params = {}) {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join('&')
  return request('/api/transactions' + (qs ? '?' + qs : ''))
}

export function buyFund(data) {
  return request('/api/transactions/buy', { method: 'POST', data: { ...data, trans_type: 'buy' } })
}

export function sellFund(data) {
  return request('/api/transactions/sell', { method: 'POST', data: { ...data, trans_type: 'sell' } })
}

export function deleteTransaction(id) {
  return request(`/api/transactions/${id}`, { method: 'DELETE' })
}

// ----------------------------------------------------------------
// 定投
// ----------------------------------------------------------------
export function listPlans(status) {
  const q = status ? `?status=${status}` : ''
  return request('/api/plans' + q)
}

export function createPlan(data) {
  return request('/api/plans', { method: 'POST', data })
}

export function updatePlan(id, data) {
  return request(`/api/plans/${id}`, { method: 'PUT', data })
}

export function deletePlan(id) {
  return request(`/api/plans/${id}`, { method: 'DELETE' })
}

// ----------------------------------------------------------------
// 管理
// ----------------------------------------------------------------
export function runDailyJob() {
  return request('/api/admin/run-daily-job', { method: 'POST' })
}

export function syncCalendar(year) {
  const q = year ? `?year=${year}` : ''
  return request('/api/admin/sync-calendar' + q, { method: 'POST' })
}
