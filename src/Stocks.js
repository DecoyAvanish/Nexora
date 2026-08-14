import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './Stocks.css';
import { 
  database, 
  doc, 
  getDoc, 
  updateDoc, 
  arrayUnion,
  arrayRemove,
  increment,
  onSnapshot,
  auth
} from './firebase';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Chart } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const FINNHUB_TOKEN = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg";
const API_BASE = 'http://localhost:5001/api';

function Stocks() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [orderType, setOrderType] = useState('market');
  const [orderQuantity, setOrderQuantity] = useState(1);
  const [orderSide, setOrderSide] = useState('buy');
  const [userCash, setUserCash] = useState(10000);
  const [userHoldings, setUserHoldings] = useState([]);
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [portfolioValue, setPortfolioValue] = useState(0);

  const searchTimeout = useRef(null);

  // Load user's portfolio and watchlist
  useEffect(() => {
    if (!auth.currentUser) return;

    const userRef = doc(database, 'users', auth.currentUser.uid);
    
    const unsubscribe = onSnapshot(userRef, (doc) => {
      if (doc.exists()) {
        const data = doc.data();
        const holdings = data.portfolio?.holdings || [];
        const cash = data.portfolio?.cash || 10000;
        
        setUserHoldings(holdings);
        setUserCash(cash);
        setWatchlist(data.watchlist || []);
        
        // Calculate portfolio value
        let totalValue = cash;
        holdings.forEach(h => {
          const price = h.lastPrice || h.avgPrice || 0;
          totalValue += price * (h.shares || 0);
        });
        setPortfolioValue(totalValue);
      }
    });

    return () => unsubscribe();
  }, []);

  const searchStocks = async (query) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/search/${query}`);
      setSearchResults(response.data.result || []);
    } catch (err) {
      console.error('Search error:', err);
      setError('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStockData = async (symbol) => {
    setLoading(true);
    setError(null);
    setOrderSuccess(null);
    try {
      const response = await axios.get(`${API_BASE}/predict/${symbol}`, {
        timeout: 15000
      });
      setStockData(response.data);
      setSelectedStock({ symbol });
    } catch (err) {
      console.error('Error fetching stock data:', err);
      
      try {
        const quoteResponse = await axios.get(
          `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_TOKEN}`
        );
        const profileResponse = await axios.get(
          `https://finnhub.io/api/v1/stock/profile2?symbol=${symbol}&token=${FINNHUB_TOKEN}`
        );
        
        if (quoteResponse.data && quoteResponse.data.c) {
          const quote = quoteResponse.data;
          const profile = profileResponse.data || {};
          
          setStockData({
            symbol: symbol,
            name: profile.name || symbol,
            last_price: quote.c,
            last_return: (quote.c - quote.pc) / quote.pc,
            predicted_return: 0,
            predicted_price: quote.c,
            confidence: 0.5,
            chart_data: {
              dates: [new Date().toISOString().split('T')[0]],
              prices: [quote.c],
              volume: [0]
            }
          });
          setSelectedStock({ symbol });
          setError(null);
        } else {
          setError(`No data found for ${symbol}`);
        }
      } catch (fallbackErr) {
        setError(`Failed to load ${symbol}: ${fallbackErr.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const buyStock = async () => {
    if (!stockData || !auth.currentUser) {
      setError('Please log in to buy stocks');
      return;
    }

    const totalCost = stockData.last_price * orderQuantity;
    
    if (totalCost > userCash) {
      setError(`Insufficient cash. You need $${totalCost.toFixed(2)} but have $${userCash.toFixed(2)}`);
      return;
    }

    setLoading(true);
    setError(null);
    setOrderSuccess(null);

    try {
      const userRef = doc(database, 'users', auth.currentUser.uid);
      const userDoc = await getDoc(userRef);
      
      if (!userDoc.exists()) {
        throw new Error('User document not found');
      }

      const userData = userDoc.data();
      const currentHoldings = userData.portfolio?.holdings || [];
      
      const existingHolding = currentHoldings.find(h => h.symbol === stockData.symbol);
      
      let updatedHoldings;
      if (existingHolding) {
        updatedHoldings = currentHoldings.map(h => {
          if (h.symbol === stockData.symbol) {
            const newShares = h.shares + orderQuantity;
            const newAvgPrice = ((h.avgPrice * h.shares) + (stockData.last_price * orderQuantity)) / newShares;
            return {
              ...h,
              shares: newShares,
              avgPrice: newAvgPrice,
              lastPrice: stockData.last_price
            };
          }
          return h;
        });
      } else {
        updatedHoldings = [
          ...currentHoldings,
          {
            symbol: stockData.symbol,
            shares: orderQuantity,
            avgPrice: stockData.last_price,
            lastPrice: stockData.last_price,
            name: stockData.name || stockData.symbol,
            purchaseDate: new Date().toISOString()
          }
        ];
      }

      await updateDoc(userRef, {
        'portfolio.cash': increment(-totalCost),
        'portfolio.holdings': updatedHoldings
      });

      if (!watchlist.includes(stockData.symbol)) {
        await updateDoc(userRef, {
          watchlist: arrayUnion(stockData.symbol)
        });
        setWatchlist([...watchlist, stockData.symbol]);
      }

      setUserCash(userCash - totalCost);
      setOrderSuccess(`✅ Bought ${orderQuantity} shares of ${stockData.symbol} for $${totalCost.toFixed(2)}`);
      setOrderQuantity(1);

    } catch (err) {
      console.error('Buy error:', err);
      setError(`Failed to buy: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sellStock = async () => {
    if (!stockData || !auth.currentUser) {
      setError('Please log in to sell stocks');
      return;
    }

    const userRef = doc(database, 'users', auth.currentUser.uid);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      setError('User not found');
      return;
    }

    const userData = userDoc.data();
    const currentHoldings = userData.portfolio?.holdings || [];
    const existingHolding = currentHoldings.find(h => h.symbol === stockData.symbol);
    
    if (!existingHolding) {
      setError(`You don't own any shares of ${stockData.symbol}`);
      return;
    }

    if (orderQuantity > existingHolding.shares) {
      setError(`You only have ${existingHolding.shares} shares to sell`);
      return;
    }

    setLoading(true);
    setError(null);
    setOrderSuccess(null);

    try {
      const totalValue = stockData.last_price * orderQuantity;
      let updatedHoldings;
      
      if (orderQuantity === existingHolding.shares) {
        updatedHoldings = currentHoldings.filter(h => h.symbol !== stockData.symbol);
      } else {
        updatedHoldings = currentHoldings.map(h => {
          if (h.symbol === stockData.symbol) {
            return {
              ...h,
              shares: h.shares - orderQuantity,
              lastPrice: stockData.last_price
            };
          }
          return h;
        });
      }

      await updateDoc(userRef, {
        'portfolio.cash': increment(totalValue),
        'portfolio.holdings': updatedHoldings
      });

      setUserCash(userCash + totalValue);
      setOrderSuccess(`✅ Sold ${orderQuantity} shares of ${stockData.symbol} for $${totalValue.toFixed(2)}`);
      setOrderQuantity(1);

    } catch (err) {
      console.error('Sell error:', err);
      setError(`Failed to sell: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const placeOrder = async () => {
    if (orderSide === 'buy') {
      await buyStock();
    } else {
      await sellStock();
    }
  };

  const toggleWatchlist = async (symbol) => {
    if (!auth.currentUser) return;
    
    const userRef = doc(database, 'users', auth.currentUser.uid);
    try {
      if (watchlist.includes(symbol)) {
        await updateDoc(userRef, {
          watchlist: arrayRemove(symbol)
        });
        setWatchlist(watchlist.filter(s => s !== symbol));
      } else {
        await updateDoc(userRef, {
          watchlist: arrayUnion(symbol)
        });
        setWatchlist([...watchlist, symbol]);
      }
    } catch (err) {
      console.error('Watchlist error:', err);
    }
  };

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (searchQuery.length > 1) {
      searchTimeout.current = setTimeout(() => searchStocks(searchQuery), 300);
    } else {
      setSearchResults([]);
    }
    return () => clearTimeout(searchTimeout.current);
  }, [searchQuery]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await axios.get(`${API_BASE}/health`);
      } catch (err) {
        console.log('API not running');
      }
    };
    checkHealth();
  }, []);

  const selectStock = (stock) => {
    setSearchQuery('');
    setSearchResults([]);
    fetchStockData(stock.symbol);
  };

  const chartData = stockData?.chart_data ? {
    labels: stockData.chart_data.dates,
    datasets: [
      {
        label: 'Price',
        data: stockData.chart_data.prices,
        borderColor: '#A855F7',
        backgroundColor: 'rgba(168, 85, 247, 0.05)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 8,
        pointHoverBackgroundColor: '#A855F7',
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2,
      },
      {
        label: 'AI Prediction',
        data: [
          ...stockData.chart_data.prices.slice(-1),
          stockData.predicted_price
        ],
        borderColor: '#A855F7',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderDash: [6, 4],
        pointRadius: [0, 12],
        pointBackgroundColor: ['transparent', '#A855F7'],
        pointBorderColor: ['transparent', '#A855F7'],
        pointHoverRadius: [0, 16],
        pointHoverBackgroundColor: ['transparent', '#A855F7'],
        pointHoverBorderColor: ['transparent', '#ffffff'],
        pointHoverBorderWidth: [0, 3],
        fill: false,
        tension: 0.4,
      }
    ]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: 'rgba(240, 237, 255, 0.4)',
          font: { size: 10, family: "'IBM Plex Mono', monospace" },
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 16,
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(8, 10, 17, 0.96)',
        titleColor: '#f0edff',
        bodyColor: '#f0edff',
        borderColor: 'rgba(168, 85, 247, 0.2)',
        borderWidth: 1,
        padding: 14,
        cornerRadius: 10,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            let value = context.parsed.y;
            if (label === 'AI Prediction' && context.dataIndex === context.dataset.data.length - 1) {
              return `🤖 ${label}: $${value.toFixed(2)}`;
            }
            return `${label}: $${value.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(168, 85, 247, 0.04)', drawBorder: false },
        ticks: { color: 'rgba(240, 237, 255, 0.15)', maxTicksLimit: 8, maxRotation: 0, font: { family: "'IBM Plex Mono', monospace", size: 8 } }
      },
      y: {
        grid: { color: 'rgba(168, 85, 247, 0.04)', drawBorder: false },
        ticks: { color: 'rgba(240, 237, 255, 0.15)', callback: (v) => '$' + v.toFixed(2), font: { family: "'IBM Plex Mono', monospace", size: 8 } }
      }
    },
    interaction: { intersect: false, mode: 'index' }
  };

  const volumeData = stockData?.chart_data ? {
    labels: stockData.chart_data.dates,
    datasets: [{
      label: 'Volume',
      data: stockData.chart_data.volume,
      backgroundColor: 'rgba(168, 85, 247, 0.12)',
      borderColor: 'rgba(168, 85, 247, 0.3)',
      borderWidth: 1,
      borderRadius: 2,
    }]
  } : null;

  const volumeOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: 'rgba(240, 237, 255, 0.15)',
          font: { size: 8, family: "'IBM Plex Mono', monospace" }
        }
      }
    },
    scales: {
      x: { display: false, grid: { display: false } },
      y: {
        grid: { color: 'rgba(168, 85, 247, 0.03)' },
        ticks: {
          color: 'rgba(240, 237, 255, 0.12)',
          callback: (v) => v >= 1e6 ? (v/1e6).toFixed(1) + 'M' : v >= 1e3 ? (v/1e3).toFixed(1) + 'K' : v,
          font: { family: "'IBM Plex Mono', monospace", size: 7 }
        }
      }
    }
  };

  const renderStockDetail = () => {
    if (!stockData) return null;

    const isInWatchlist = watchlist.includes(stockData.symbol);
    const change = stockData.last_return * 100;
    const isPositive = change >= 0;
    const totalCost = stockData.last_price * orderQuantity;
    const hasEnoughCash = totalCost <= userCash;
    const currentHolding = userHoldings.find(h => h.symbol === stockData.symbol);
    const maxSellShares = currentHolding?.shares || 0;

    return (
      <div className="stock-detail">
        <div className="stock-header">
          <div className="stock-info">
            <div className="stock-symbol-badge">
              <span className="symbol">{stockData.symbol}</span>
              <span className="exchange">NASDAQ</span>
            </div>
            <span className="stock-name">{stockData.name || stockData.symbol}</span>
          </div>
          <div className="stock-price">
            <span className="current-price">${stockData.last_price?.toFixed(2)}</span>
            <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
              {isPositive ? '↑' : '↓'} {Math.abs(change).toFixed(2)}%
            </span>
            <button
              className={`watchlist-btn ${isInWatchlist ? 'active' : ''}`}
              onClick={() => toggleWatchlist(stockData.symbol)}
            >
              {isInWatchlist ? '★' : '☆'}
            </button>
          </div>
        </div>

        <div style={{
          background: 'rgba(168, 85, 247, 0.03)',
          border: '1px solid rgba(168, 85, 247, 0.06)',
          borderRadius: '10px',
          padding: '12px 16px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: "'IBM Plex Mono', monospace"
        }}>
          <span style={{ color: 'rgba(240, 237, 255, 0.5)', fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase' }}>
            💰 Buying Power
          </span>
          <span style={{ color: '#f0edff', fontSize: '18px', fontWeight: '700' }}>
            ${userCash.toFixed(2)}
          </span>
        </div>

        {currentHolding && (
          <div style={{
            background: 'rgba(75, 255, 155, 0.03)',
            border: '1px solid rgba(75, 255, 155, 0.1)',
            borderRadius: '10px',
            padding: '12px 16px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '12px'
          }}>
            <span style={{ color: 'rgba(240, 237, 255, 0.5)' }}>
              📈 Current Holding
            </span>
            <span style={{ color: '#4bff9b' }}>
              {currentHolding.shares} shares @ ${currentHolding.avgPrice.toFixed(2)}
            </span>
          </div>
        )}

        {orderSuccess && (
          <div style={{
            padding: '12px 16px',
            background: 'rgba(75, 255, 155, 0.06)',
            border: '1px solid rgba(75, 255, 155, 0.18)',
            borderRadius: '10px',
            color: '#4bff9b',
            marginBottom: '16px',
            fontSize: '13px',
            fontFamily: "'IBM Plex Mono', monospace"
          }}>
            {orderSuccess}
          </div>
        )}

        <div className="charts-container">
          <div className="price-chart">
            <Chart type="line" data={chartData} options={chartOptions} />
          </div>
          {volumeData && (
            <div className="volume-chart">
              <Chart type="bar" data={volumeData} options={volumeOptions} />
            </div>
          )}
        </div>

        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-label">Open</span>
            <span className="stat-value">${(stockData.last_price * 0.98).toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">High</span>
            <span className="stat-value">${(stockData.last_price * 1.03).toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Low</span>
            <span className="stat-value">${(stockData.last_price * 0.97).toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Volume</span>
            <span className="stat-value">{stockData.chart_data?.volume?.slice(-1)[0]?.toLocaleString() || 'N/A'}</span>
          </div>
        </div>

        <div className="prediction-section">
          <div className="prediction-header">
            <span className="prediction-icon">🧠</span>
            <span className="prediction-title">AI FORECAST</span>
            <span className="confidence-badge">
              {((stockData.confidence || 0.85) * 100).toFixed(0)}% confidence
            </span>
          </div>
          <div className="prediction-grid">
            <div className="prediction-card">
              <span className="prediction-label">Current</span>
              <span className="prediction-value">${stockData.last_price?.toFixed(2)}</span>
            </div>
            <div className="prediction-card highlight">
              <span className="prediction-label">Predicted</span>
              <span className="prediction-value predicted">${stockData.predicted_price?.toFixed(2)}</span>
            </div>
            <div className="prediction-card">
              <span className="prediction-label">Return</span>
              <span className={`prediction-value ${stockData.predicted_return >= 0 ? 'positive' : 'negative'}`}>
                {(stockData.predicted_return * 100).toFixed(2)}%
              </span>
            </div>
          </div>
          <div className="prediction-note">
            LSTM neural network • {stockData.chart_data?.dates?.length || 0} training samples
          </div>
        </div>

        <div className="trading-panel">
          <div className="order-toggle">
            <button 
              className={`order-btn buy ${orderSide === 'buy' ? 'active' : ''}`} 
              onClick={() => setOrderSide('buy')}
            >
              <span className="btn-icon">▲</span> Buy
            </button>
            <button 
              className={`order-btn sell ${orderSide === 'sell' ? 'active' : ''}`} 
              onClick={() => setOrderSide('sell')}
              style={{ opacity: (!currentHolding || currentHolding.shares === 0) ? 0.3 : 1 }}
            >
              <span className="btn-icon">▼</span> Sell
            </button>
          </div>
          <div className="order-controls">
            <div className="qty-control">
              <button onClick={() => setOrderQuantity(Math.max(1, orderQuantity - 1))}>−</button>
              <input 
                type="number" 
                value={orderQuantity} 
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  const max = orderSide === 'sell' ? maxSellShares : 999;
                  setOrderQuantity(Math.max(1, Math.min(val || 1, max)));
                }} 
                min="1" 
                max={orderSide === 'sell' ? maxSellShares : 999}
              />
              <button onClick={() => {
                const max = orderSide === 'sell' ? maxSellShares : 999;
                setOrderQuantity(Math.min(orderQuantity + 1, max));
              }}>+</button>
            </div>
            <select className="order-type" value={orderType} onChange={(e) => setOrderType(e.target.value)}>
              <option value="market">Market</option>
              <option value="limit">Limit</option>
              <option value="stop">Stop</option>
            </select>
          </div>
          <div className="order-total">
            <span>Total</span>
            <span className="total-price">${totalCost.toFixed(2)}</span>
          </div>
          <button 
            className={`place-order ${orderSide}`} 
            onClick={placeOrder} 
            disabled={loading || (orderSide === 'buy' && !hasEnoughCash) || (orderSide === 'sell' && orderQuantity > maxSellShares)}
          >
            {loading ? '⏳ Processing' : 
             orderSide === 'buy' ? 
               (hasEnoughCash ? `Buy ${orderQuantity} shares` : 'Insufficient Funds') :
               `Sell ${orderQuantity} shares`}
          </button>
          {orderSide === 'sell' && currentHolding && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: '8px', 
              fontSize: '10px', 
              color: 'rgba(240, 237, 255, 0.2)',
              fontFamily: "'IBM Plex Mono', monospace"
            }}>
              Max: {maxSellShares} shares
            </div>
          )}
        </div>
      </div>
    );
  };

  const particles = Array.from({ length: 25 }, (_, i) => ({
    id: i,
    delay: i * 1.1,
    duration: 22 + Math.random() * 18,
    x: Math.random() * 100,
    size: 0.8 + Math.random() * 2,
    startY: 20 + Math.random() * 80
  }));

  return (
    <div className="stocks-container">
      <div className="bg-grid"></div>
      <div className="bg-orbitals">
        <div className="orbital-ring ring-1"></div>
        <div className="orbital-ring ring-2"></div>
        <div className="orbital-ring ring-3"></div>
        <div className="orbital-dot dot-1"></div>
        <div className="orbital-dot dot-2"></div>
        <div className="orbital-dot dot-3"></div>
      </div>
      <div className="bg-chartlines">
        <svg viewBox="0 0 1000 700" preserveAspectRatio="none">
          <polyline points="0,520 120,500 220,460 300,480 420,380 540,410 640,300 760,330 860,220 1000,250" fill="none" stroke="rgba(168,85,247,0.2)" strokeWidth="1.5" />
          <polyline points="0,180 140,210 260,160 380,190 500,120 620,150 740,90 860,110 1000,60" fill="none" stroke="rgba(168,85,247,0.1)" strokeWidth="1" />
          <circle cx="300" cy="480" r="3" fill="rgba(168,85,247,0.15)" />
          <circle cx="640" cy="300" r="2" fill="rgba(168,85,247,0.1)" />
          <circle cx="860" cy="220" r="4" fill="rgba(168,85,247,0.08)" />
        </svg>
      </div>
      <div className="bg-particles">
        {particles.map((p) => (
          <div key={p.id} className="bg-particle" style={{
            '--delay': `${p.delay}s`,
            '--duration': `${p.duration}s`,
            '--x': `${p.x}%`,
            '--size': `${p.size}px`,
            '--start-y': `${p.startY}%`,
          }}></div>
        ))}
      </div>
      <div className="bg-scanline"></div>

      <div className="terminal-header">
        <div className="terminal-brand">
          <span className="brand-dot">●</span>
          <span className="brand-name">NEXORA</span>
          <span className="brand-sep">//</span>
          <span className="brand-module">MARKET</span>
        </div>
        <div className="terminal-status">
          <span className="status-ping"></span>
          <span className="status-text">LIVE</span>
          <span className="status-time">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="search-section">
        <div className="search-wrap">
          <span className="search-icon">⌕</span>
          <input
            type="text"
            placeholder="Enter symbol (AAPL, MSFT, TSLA...)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          {loading && <span className="search-spinner">⟳</span>}
        </div>
        {searchResults.length > 0 && (
          <div className="search-dropdown">
            {searchResults.map((stock) => (
              <div key={stock.symbol} className="search-result" onClick={() => selectStock(stock)}>
                <span className="result-symbol">{stock.symbol}</span>
                <span className="result-name">{stock.description}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {selectedStock ? (
        renderStockDetail()
      ) : (
        <div className="empty-state">
          <div className="empty-graphic">
            <span className="empty-icon">📊</span>
            <div className="empty-chart-bars">
              {[...Array(16)].map((_, i) => (
                <div key={i} className="empty-bar" style={{ height: `${15 + Math.random() * 70}%` }}></div>
              ))}
            </div>
          </div>
          <h2>Search for a stock</h2>
          <p>Get AI-powered predictions and real-time market data</p>
          <div className="quick-stocks">
            <span>Quick access:</span>
            {['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'NVDA'].map((symbol) => (
              <button key={symbol} className="quick-btn" onClick={() => selectStock({ symbol })}>
                {symbol}
              </button>
            ))}
          </div>
        </div>
      )}

      {watchlist.length > 0 && (
        <div className="watchlist-section">
          <div className="watchlist-header">
            <span>⭐ WATCHLIST</span>
            <span className="watchlist-count">{watchlist.length} symbols</span>
          </div>
          <div className="watchlist-items">
            {watchlist.map((symbol) => (
              <div key={symbol} className="watchlist-item" onClick={() => selectStock({ symbol })}>
                {symbol}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Stocks;