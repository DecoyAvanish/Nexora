import React, { useState } from 'react'
import './Cash.css'

const Cash = () => {
  const [balance, setBalance] = useState(114656.00)
  const [buyingPower, setBuyingPower] = useState(4110.00)
  const [cashAvailable, setCashAvailable] = useState(2850.50)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [depositAmount, setDepositAmount] = useState('')
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('bank')
  const [showDepositModal, setShowDepositModal] = useState(false)
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
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

  const [currency, setCurrency] = useState('USD')
  const [defaultPayment, setDefaultPayment] = useState(1)

  const handleDeposit = () => {
    const amount = parseFloat(depositAmount)
    if (amount > 0) {
      const newTransaction = {
        id: transactionHistory.length + 1,
        type: 'deposit',
        amount: amount,
        date: new Date().toISOString().split('T')[0],
        status: 'pending',
        method: selectedPaymentMethod === 'bank' ? 'Bank Transfer' : 
                selectedPaymentMethod === 'card' ? 'Credit Card' : 'Wire Transfer'
      }
      setTransactionHistory([newTransaction, ...transactionHistory])
      setCashAvailable(cashAvailable + amount)
      setDepositAmount('')
      setShowDepositModal(false)
    }
  }

  const handleWithdraw = () => {
    const amount = parseFloat(withdrawAmount)
    if (amount > 0 && amount <= cashAvailable) {
      const newTransaction = {
        id: transactionHistory.length + 1,
        type: 'withdraw',
        amount: amount,
        date: new Date().toISOString().split('T')[0],
        status: 'pending',
        method: 'Bank Transfer'
      }
      setTransactionHistory([newTransaction, ...transactionHistory])
      setCashAvailable(cashAvailable - amount)
      setWithdrawAmount('')
      setShowWithdrawModal(false)
    }
  }

  const getTotalAssets = () => {
    return balance + buyingPower + cashAvailable
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
              <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                <option value="USD">USD $</option>
                <option value="EUR">EUR €</option>
                <option value="GBP">GBP £</option>
                <option value="JPY">JPY ¥</option>
              </select>
            </span>
          </div>
        </div>

        <div className="balance-overview">
          <div className="balance-card total">
            <div className="balance-label">Total Assets</div>
            <div className="balance-amount">${getTotalAssets().toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            <div className="balance-change positive">+12.4% this month</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Portfolio Value</div>
            <div className="balance-amount">${balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            <div className="balance-change positive">+$44.63 today</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Buying Power</div>
            <div className="balance-amount">${buyingPower.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            <div className="balance-change neutral">Available to trade</div>
          </div>
          <div className="balance-card">
            <div className="balance-label">Cash Available</div>
            <div className="balance-amount">${cashAvailable.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
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
                    {transaction.type === 'deposit' ? '+' : '-'}${transaction.amount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
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
                <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  <option value="USD">United States Dollar (USD)</option>
                  <option value="EUR">Euro (EUR)</option>
                  <option value="GBP">British Pound (GBP)</option>
                  <option value="JPY">Japanese Yen (JPY)</option>
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
                  <label>Amount (USD)</label>
                  <input 
                    type="number" 
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder="0.00"
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
                  <label>Amount (USD)</label>
                  <input 
                    type="number" 
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    placeholder="0.00"
                    className="modal-input"
                  />
                  <small>Available: ${cashAvailable.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</small>
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