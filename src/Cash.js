import React, { useState, useEffect } from 'react'
import './Cash.css'

const currencies = [
  { code: 'USD', symbol: '$', name: 'US Dollar', rate: 1 },
  { code: 'EUR', symbol: '€', name: 'Euro', rate: 0.92 },
  { code: 'GBP', symbol: '£', name: 'British Pound', rate: 0.79 },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen', rate: 149.50 },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', rate: 1.54 },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', rate: 1.37 },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc', rate: 0.88 },
  { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', rate: 7.18 },
  { code: 'HKD', symbol: 'HK$', name: 'Hong Kong Dollar', rate: 7.81 },
  { code: 'NZD', symbol: 'NZ$', name: 'New Zealand Dollar', rate: 1.68 },
  { code: 'SEK', symbol: 'kr', name: 'Swedish Krona', rate: 10.82 },
  { code: 'KRW', symbol: '₩', name: 'South Korean Won', rate: 1375.00 },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', rate: 1.36 },
  { code: 'NOK', symbol: 'kr', name: 'Norwegian Krone', rate: 10.95 },
  { code: 'MXN', symbol: 'Mex$', name: 'Mexican Peso', rate: 16.75 },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee', rate: 83.50 },
  { code: 'RUB', symbol: '₽', name: 'Russian Ruble', rate: 92.30 },
  { code: 'ZAR', symbol: 'R', name: 'South African Rand', rate: 18.90 },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real', rate: 5.05 },
  { code: 'TRY', symbol: '₺', name: 'Turkish Lira', rate: 32.80 },
  { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham', rate: 3.67 },
  { code: 'SAR', symbol: '﷼', name: 'Saudi Riyal', rate: 3.75 },
  { code: 'PLN', symbol: 'zł', name: 'Polish Zloty', rate: 4.12 },
  { code: 'THB', symbol: '฿', name: 'Thai Baht', rate: 36.80 },
  { code: 'MYR', symbol: 'RM', name: 'Malaysian Ringgit', rate: 4.75 },
  { code: 'PHP', symbol: '₱', name: 'Philippine Peso', rate: 57.50 },
  { code: 'IDR', symbol: 'Rp', name: 'Indonesian Rupiah', rate: 16050 },
  { code: 'VND', symbol: '₫', name: 'Vietnamese Dong', rate: 25450 },
  { code: 'EGP', symbol: 'E£', name: 'Egyptian Pound', rate: 48.20 },
  { code: 'NGN', symbol: '₦', name: 'Nigerian Naira', rate: 1580 },
  { code: 'PKR', symbol: 'Rs', name: 'Pakistani Rupee', rate: 278.50 },
  { code: 'BDT', symbol: '৳', name: 'Bangladeshi Taka', rate: 117.50 },
  { code: 'KWD', symbol: 'KD', name: 'Kuwaiti Dinar', rate: 0.31 },
  { code: 'BHD', symbol: '.د.ب', name: 'Bahraini Dinar', rate: 0.38 },
  { code: 'OMR', symbol: '﷼', name: 'Omani Rial', rate: 0.38 },
  { code: 'QAR', symbol: '﷼', name: 'Qatari Riyal', rate: 3.64 },
  { code: 'DKK', symbol: 'kr', name: 'Danish Krone', rate: 6.94 },
  { code: 'HUF', symbol: 'Ft', name: 'Hungarian Forint', rate: 365 },
  { code: 'CZK', symbol: 'Kč', name: 'Czech Koruna', rate: 23.40 },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel', rate: 3.72 },
  { code: 'CLP', symbol: '$', name: 'Chilean Peso', rate: 970 },
  { code: 'COP', symbol: '$', name: 'Colombian Peso', rate: 3950 },
  { code: 'PEN', symbol: 'S/', name: 'Peruvian Sol', rate: 3.82 },
  { code: 'ARS', symbol: '$', name: 'Argentine Peso', rate: 880 },
]

const Cash = () => {
  const [baseBalance] = useState(114656.00)
  const [baseBuyingPower] = useState(4110.00)
  const [baseCashAvailable] = useState(2850.50)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [depositAmount, setDepositAmount] = useState('')
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('bank')
  const [showDepositModal, setShowDepositModal] = useState(false)
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
  const [selectedCurrency, setSelectedCurrency] = useState(() => {
    const saved = localStorage.getItem('preferredCurrency')
    return saved || 'USD'
  })
  
  const [transactionHistory, setTransactionHistory] = useState([
    { id: 1, type: 'deposit', amount: 5000, date: '2026-08-10', status: 'completed', method: 'Bank Transfer' },
    { id: 2, type: 'withdraw', amount: 2000, date: '2026-08-08', status: 'completed', method: 'Bank Transfer' },
    { id: 3, type: 'deposit', amount: 1000, date: '2026-08-05', status: 'pending', method: 'Credit Card' },
    { id: 4, type: 'deposit', amount: 3000, date: '2026-08-01', status: 'completed', method: 'Wire Transfer' },
    { id: 5, type: 'withdraw', amount: 1500, date: '2026-07-28', status: 'completed', method: 'Bank Transfer' },
  ])

  const [paymentMethods, setPaymentMethods] = useState([
    { id: 1, type: 'Bank Account', name: 'Chase Bank', last4: '4829', default: true },
    { id: 2, type: 'Credit Card', name: 'Visa', last4: '2345', default: false },
    { id: 3, type: 'Wire Transfer', name: 'Wells Fargo', last4: '6781', default: false },
  ])

  const [defaultPayment, setDefaultPayment] = useState(1)

  const currentCurrency = currencies.find(c => c.code === selectedCurrency) || currencies[0]
  const exchangeRate = currentCurrency.rate

  const convertAmount = (amount) => {
    return amount * exchangeRate
  }

  const formatCurrency = (amount) => {
    const converted = convertAmount(amount)
    const symbol = currentCurrency.symbol
    
    if (selectedCurrency === 'JPY' || selectedCurrency === 'KRW' || selectedCurrency === 'IDR' || selectedCurrency === 'VND') {
      return `${symbol}${Math.round(converted).toLocaleString()}`
    }
    
    if (selectedCurrency === 'KWD' || selectedCurrency === 'BHD' || selectedCurrency === 'OMR') {
      return `${symbol}${converted.toFixed(3)}`
    }
    
    return `${symbol}${converted.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatAmount = (amount, showSymbol = true) => {
    if (showSymbol) {
      return formatCurrency(amount)
    }
    const converted = convertAmount(amount)
    return converted.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  useEffect(() => {
    localStorage.setItem('preferredCurrency', selectedCurrency)
  }, [selectedCurrency])

  const handleDeposit = () => {
    const amount = parseFloat(depositAmount)
    if (amount > 0) {
      const newTransaction = {
        id: transactionHistory.length + 1,
        type: 'deposit',
        amount: amount / exchangeRate,
        date: new Date().toISOString().split('T')[0],
        status: 'pending',
        method: selectedPaymentMethod === 'bank' ? 'Bank Transfer' : 
                selectedPaymentMethod === 'card' ? 'Credit Card' : 'Wire Transfer'
      }
      setTransactionHistory([newTransaction, ...transactionHistory])
      setDepositAmount('')
      setShowDepositModal(false)
    }
  }

  const handleWithdraw = () => {
    const amount = parseFloat(withdrawAmount)
    const convertedAmount = amount / exchangeRate
    if (amount > 0 && convertedAmount <= baseCashAvailable) {
      const newTransaction = {
        id: transactionHistory.length + 1,
        type: 'withdraw',
        amount: convertedAmount,
        date: new Date().toISOString().split('T')[0],
        status: 'pending',
        method: 'Bank Transfer'
      }
      setTransactionHistory([newTransaction, ...transactionHistory])
      setWithdrawAmount('')
      setShowWithdrawModal(false)
    }
  }

  const getTotalAssets = () => {
    return baseBalance + baseBuyingPower + baseCashAvailable
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'status-completed'
      case 'pending': return 'status-pending'
      case 'failed': return 'status-failed'
      default: return ''
    }
  }

  const getTypeColor = (type) => {
    return type === 'deposit' ? 'type-deposit' : 'type-withdraw'
  }

  return (
    <div className="cash-page">
      <div className="cash-container">
        <div className="cash-header">
          <h1>Cash Management</h1>
          <div className="cash-header-actions">
            <span className="currency-selector">
              <select 
                value={selectedCurrency} 
                onChange={(e) => setSelectedCurrency(e.target.value)}
                className="currency-select"
              >
                {currencies.map(currency => (
                  <option key={currency.code} value={currency.code}>
                    {currency.code} - {currency.name} ({currency.symbol})
                  </option>
                ))}
              </select>
            </span>
          </div>
        </div>

        <div className="balance-overview">
          <div className="balance-card total">
            <div className="balance-label">Total Assets</div>
            <div className="balance-amount">{formatCurrency(getTotalAssets())}</div>
            <div className="balance-change positive">+12.4% this month</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Portfolio Value</div>
            <div className="balance-amount">{formatCurrency(baseBalance)}</div>
            <div className="balance-change positive">+{formatCurrency(44.63)} today</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Buying Power</div>
            <div className="balance-amount">{formatCurrency(baseBuyingPower)}</div>
            <div className="balance-change neutral">Available to trade</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Cash Available</div>
            <div className="balance-amount">{formatCurrency(baseCashAvailable)}</div>
            <div className="balance-change neutral">Ready to withdraw</div>
          </div>
        </div>

        <div className="quick-actions">
          <button className="action-btn deposit" onClick={() => setShowDepositModal(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="16"/>
              <line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
            Deposit Funds
          </button>
          <button className="action-btn withdraw" onClick={() => setShowWithdrawModal(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="16"/>
              <line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
            Withdraw Funds
          </button>
          <button className="action-btn transfer">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 1l4 4-4 4"/>
              <path d="M3 11V9a4 4 0 014-4h14"/>
              <path d="M7 23l-4-4 4-4"/>
              <path d="M21 13v2a4 4 0 01-4 4H3"/>
            </svg>
            Transfer
          </button>
          <button className="action-btn history">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            History
          </button>
        </div>

        <div className="payment-section">
          <div className="section-header">
            <h2>Payment Methods</h2>
            <button className="add-method-btn">+ Add New</button>
          </div>
          <div className="payment-methods">
            {paymentMethods.map(method => (
              <div key={method.id} className={`payment-card ${method.default ? 'default' : ''}`}>
                <div className="payment-info">
                  <div className="payment-icon">
                    {method.type === 'Bank Account' && '🏦'}
                    {method.type === 'Credit Card' && '💳'}
                    {method.type === 'Wire Transfer' && '🌐'}
                  </div>
                  <div className="payment-details">
                    <div className="payment-name">{method.name}</div>
                    <div className="payment-type">•••• {method.last4}</div>
                  </div>
                </div>
                <div className="payment-actions">
                  {method.default && <span className="default-badge">Default</span>}
                  <button className="payment-action-btn">Edit</button>
                  <button className="payment-action-btn">Remove</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="transaction-section">
          <div className="section-header">
            <h2>Transaction History</h2>
            <select className="filter-select">
              <option value="all">All Transactions</option>
              <option value="deposit">Deposits</option>
              <option value="withdraw">Withdrawals</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div className="transaction-list">
            {transactionHistory.map(transaction => (
              <div key={transaction.id} className="transaction-item">
                <div className="transaction-left">
                  <div className={`transaction-icon ${getTypeColor(transaction.type)}`}>
                    {transaction.type === 'deposit' ? '↓' : '↑'}
                  </div>
                  <div className="transaction-details">
                    <div className="transaction-type">
                      {transaction.type === 'deposit' ? 'Deposit' : 'Withdrawal'}
                    </div>
                    <div className="transaction-meta">
                      <span>{transaction.method}</span>
                      <span>•</span>
                      <span>{transaction.date}</span>
                    </div>
                  </div>
                </div>
                <div className="transaction-right">
                  <div className={`transaction-amount ${getTypeColor(transaction.type)}`}>
                    {transaction.type === 'deposit' ? '+' : '-'}{formatCurrency(transaction.amount)}
                  </div>
                  <div className={`transaction-status ${getStatusColor(transaction.status)}`}>
                    {transaction.status}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <h2>Cash Settings</h2>
          </div>
          <div className="settings-grid">
            <div className="setting-item">
              <div className="setting-label">Default Currency</div>
              <div className="setting-value">
                <select 
                  value={selectedCurrency} 
                  onChange={(e) => setSelectedCurrency(e.target.value)}
                  className="setting-select"
                >
                  {currencies.map(currency => (
                    <option key={currency.code} value={currency.code}>
                      {currency.code} - {currency.name} ({currency.symbol})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="setting-item">
              <div className="setting-label">Auto-Transfer</div>
              <div className="setting-value">
                <label className="toggle-switch">
                  <input type="checkbox" />
                  <span className="toggle-slider"></span>
                </label>
                <span className="setting-description">Auto-transfer to bank</span>
              </div>
            </div>
            <div className="setting-item">
              <div className="setting-label">Minimum Balance Alert</div>
              <div className="setting-value">
                <input type="number" placeholder="Set minimum balance" className="setting-input" />
                <span className="setting-description">Alert when below</span>
              </div>
            </div>
            <div className="setting-item">
              <div className="setting-label">Daily Withdrawal Limit</div>
              <div className="setting-value">
                <input type="number" placeholder="Set daily limit" className="setting-input" />
                <span className="setting-description">Per day</span>
              </div>
            </div>
          </div>
        </div>

        {showDepositModal && (
          <div className="modal-overlay" onClick={() => setShowDepositModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Deposit Funds</h2>
                <button className="modal-close" onClick={() => setShowDepositModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <div className="modal-input-group">
                  <label>Amount ({currentCurrency.code})</label>
                  <input 
                    type="number" 
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder={`0.00 ${currentCurrency.code}`}
                    className="modal-input"
                  />
                </div>
                <div className="modal-input-group">
                  <label>Payment Method</label>
                  <select 
                    value={selectedPaymentMethod} 
                    onChange={(e) => setSelectedPaymentMethod(e.target.value)}
                    className="modal-select"
                  >
                    <option value="bank">Bank Transfer</option>
                    <option value="card">Credit Card</option>
                    <option value="wire">Wire Transfer</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button className="modal-btn cancel" onClick={() => setShowDepositModal(false)}>Cancel</button>
                  <button className="modal-btn confirm" onClick={handleDeposit}>Confirm Deposit</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showWithdrawModal && (
          <div className="modal-overlay" onClick={() => setShowWithdrawModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Withdraw Funds</h2>
                <button className="modal-close" onClick={() => setShowWithdrawModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <div className="modal-input-group">
                  <label>Amount ({currentCurrency.code})</label>
                  <input 
                    type="number" 
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    placeholder={`0.00 ${currentCurrency.code}`}
                    className="modal-input"
                  />
                  <small>Available: {formatCurrency(baseCashAvailable)}</small>
                </div>
                <div className="modal-input-group">
                  <label>Bank Account</label>
                  <select className="modal-select">
                    <option>Chase Bank •••• 4829</option>
                    <option>Wells Fargo •••• 6781</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button className="modal-btn cancel" onClick={() => setShowWithdrawModal(false)}>Cancel</button>
                  <button className="modal-btn confirm" onClick={handleWithdraw}>Confirm Withdrawal</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Cash