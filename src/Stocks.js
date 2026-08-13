// Stocks.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './Stocks.css';
import { database } from './firebase';
import { doc, setDoc, getDoc } from 'firebase/firestore';
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

// API calls to your backend (no API key here!)
const API_BASE = 'http://localhost:5001/api';

function Stocks() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [watchlist, setWatchlist] = useState(['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN']);
  const [orderType, setOrderType] = useState('market');
  const [orderQuantity, setOrderQuantity] = useState(1);
  const [orderSide, setOrderSide] = useState('buy');

  const searchTimeout = useRef(null);

  // Search stocks
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

  // Fetch stock data with prediction
  const fetchStockData = async (symbol) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/predict/${symbol}`);
      setStockData(response.data);
      setSelectedStock({ symbol });
    } catch (err) {
      console.error('Error fetching stock data:', err);
      setError(err.response?.data?.error || 'Failed to load stock data');
    } finally {
      setLoading(false);
    }
  };

  // Search with debounce
  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (searchQuery.length > 1) {
      searchTimeout.current = setTimeout(() => searchStocks(searchQuery), 300);
    } else {
      setSearchResults([]);
    }
    return () => clearTimeout(searchTimeout.current);
  }, [searchQuery]);

  // Check API health on load
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`);
        console.log('API Health:', response.data);
      } catch (err) {
        console.error('API not running! Make sure to start the backend:', err);
        setError('Backend server not running. Please start the prediction API.');
      }
    };
    checkHealth();
  }, []);

  // Chart configuration
  const chartData = stockData?.chart_data ? {
    labels: stockData.chart_data.dates,
    datasets: [
      {
        label: 'Historical Price',
        data: stockData.chart_data.prices,
        borderColor: '#5AC53B',
        backgroundColor: 'rgba(90, 197, 59, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#5AC53B',
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2,
      },
      {
        label: 'AI Prediction',
        data: [
          ...stockData.chart_data.prices.slice(-1),
          stockData.predicted_price
        ],
        borderColor: '#FF6B6B',
        backgroundColor: 'rgba(255, 107, 107, 0.2)',
        borderDash: [8, 4],
        pointRadius: [0, 10],
        pointBackgroundColor: ['transparent', '#FF6B6B'],
        pointBorderColor: ['transparent', '#FF6B6B'],
        pointHoverRadius: [0, 12],
        pointHoverBackgroundColor: ['transparent', '#FF6B6B'],
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
          color: '#e0e0e0',
          font: { size: 12 },
          usePointStyle: true,
          pointStyle: 'circle',
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(20, 20, 20, 0.95)',
        titleColor: '#e0e0e0',
        bodyColor: '#e0e0e0',
        borderColor: '#333',
        borderWidth: 1,
        padding: 12,
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
        grid: {
          color: 'rgba(59, 71, 84, 0.2)',
          drawBorder: false,
        },
        ticks: {
          color: '#7B858A',
          maxTicksLimit: 10,
          maxRotation: 0,
        }
      },
      y: {
        grid: {
          color: 'rgba(59, 71, 84, 0.2)',
          drawBorder: false,
        },
        ticks: {
          color: '#7B858A',
          callback: function(value) {
            return '$' + value.toFixed(2);
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    }
  };

  // Volume chart
  const volumeData = stockData?.chart_data ? {
    labels: stockData.chart_data.dates,
    datasets: [{
      label: 'Volume',
      data: stockData.chart_data.volume,
      backgroundColor: 'rgba(90, 197, 59, 0.2)',
      borderColor: 'rgba(90, 197, 59, 0.4)',
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
          color: '#7B858A',
          font: { size: 10 }
        }
      }
    },
    scales: {
      x: {
        display: false,
        grid: { display: false }
      },
      y: {
        grid: {
          color: 'rgba(59, 71, 84, 0.2)',
        },
        ticks: {
          color: '#7B858A',
          callback: function(value) {
            if (value >= 1e9) return (value / 1e9).toFixed(1) + 'B';
            if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
            if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
            return value;
          }
        }
      }
    }
  };

  const selectStock = (stock) => {
    setSearchQuery('');
    setSearchResults([]);
    fetchStockData(stock.symbol);
  };

  const addToWatchlist = async (symbol) => {
    if (!watchlist.includes(symbol)) {
      const newWatchlist = [...watchlist, symbol];
      setWatchlist(newWatchlist);
      try {
        const userId = 'demoUser';
        const watchlistRef = doc(database, 'users', userId, 'watchlist', 'stocks');
        await setDoc(watchlistRef, { symbols: newWatchlist });
      } catch (err) {
        console.error('Error saving watchlist:', err);
      }
    }
  };

  const removeFromWatchlist = async (symbol) => {
    const newWatchlist = watchlist.filter(s => s !== symbol);
    setWatchlist(newWatchlist);
    try {
      const userId = 'demoUser';
      const watchlistRef = doc(database, 'users', userId, 'watchlist', 'stocks');
      await setDoc(watchlistRef, { symbols: newWatchlist });
    } catch (err) {
      console.error('Error saving watchlist:', err);
    }
  };

  const placeOrder = async () => {
    if (!stockData) return;
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`✅ Successfully ${orderSide} ${orderQuantity} shares of ${stockData.symbol}`);
    } catch (err) {
      setError('Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  // Render stock detail view
  const renderStockDetail = () => {
    if (!stockData) return null;

    const isInWatchlist = watchlist.includes(stockData.symbol);
    const change = stockData.last_return * 100;
    const isPositive = change >= 0;

    return (
      <div className="stock-detail">
        <div className="stock-header">
          <div className="stock-info">
            <div>
              <h2>{stockData.symbol}</h2>
              <span className="stock-name">{stockData.name || stockData.symbol}</span>
            </div>
            <button
              className={`watchlist-btn ${isInWatchlist ? 'active' : ''}`}
              onClick={() => isInWatchlist ? removeFromWatchlist(stockData.symbol) : addToWatchlist(stockData.symbol)}
            >
              {isInWatchlist ? '⭐' : '☆'}
            </button>
          </div>
          <div className="stock-price">
            <span className="current-price">${stockData.last_price?.toFixed(2)}</span>
            <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
              {isPositive ? '+' : ''}{change.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Charts */}
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

        {/* Prediction Info */}
        <div className="prediction-section">
          <div className="prediction-header">
            <span className="prediction-icon">🤖</span>
            <h3>AI Price Prediction</h3>
            <span className="confidence-badge">
              Confidence: {(stockData.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="prediction-grid">
            <div className="prediction-card">
              <span className="prediction-label">Current Price</span>
              <span className="prediction-value">${stockData.last_price?.toFixed(2)}</span>
            </div>
            <div className="prediction-card highlight">
              <span className="prediction-label">Predicted Price</span>
              <span className="prediction-value predicted">
                ${stockData.predicted_price?.toFixed(2)}
              </span>
            </div>
            <div className="prediction-card">
              <span className="prediction-label">Expected Change</span>
              <span className={`prediction-value ${stockData.predicted_return >= 0 ? 'positive' : 'negative'}`}>
                {(stockData.predicted_return * 100).toFixed(2)}%
              </span>
            </div>
          </div>
          <div className="prediction-note">
            ⚡ Based on LSTM neural network trained on historical price patterns
          </div>
        </div>

        {/* Trading Panel */}
        <div className="trading-panel">
          <div className="order-type-toggle">
            <button 
              className={`order-btn buy ${orderSide === 'buy' ? 'active' : ''}`}
              onClick={() => setOrderSide('buy')}
            >
              Buy
            </button>
            <button 
              className={`order-btn sell ${orderSide === 'sell' ? 'active' : ''}`}
              onClick={() => setOrderSide('sell')}
            >
              Sell
            </button>
          </div>
          <div className="order-controls">
            <div className="order-quantity">
              <button onClick={() => setOrderQuantity(Math.max(1, orderQuantity - 1))}>−</button>
              <input 
                type="number" 
                value={orderQuantity} 
                onChange={(e) => setOrderQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                min="1"
              />
              <button onClick={() => setOrderQuantity(orderQuantity + 1)}>+</button>
            </div>
            <div className="order-type-select">
              <select value={orderType} onChange={(e) => setOrderType(e.target.value)}>
                <option value="market">Market Order</option>
                <option value="limit">Limit Order</option>
                <option value="stop">Stop Order</option>
              </select>
            </div>
          </div>
          <div className="order-total">
            <span>Total</span>
            <span className="total-price">
              ${(stockData.last_price * orderQuantity).toFixed(2)}
            </span>
          </div>
          <button 
            className={`place-order-btn ${orderSide}`} 
            onClick={placeOrder}
            disabled={loading}
          >
            {loading ? 'Processing...' : `${orderSide === 'buy' ? 'Buy' : 'Sell'} ${orderQuantity} shares`}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="stocks-page">
      {/* Search Section */}
      <div className="search-section">
        <div className="search-container">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search stocks (AAPL, MSFT, TSLA)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          {loading && <span className="search-loading">⏳</span>}
        </div>
        
        {searchResults.length > 0 && (
          <div className="search-results">
            {searchResults.map((stock) => (
              <div 
                key={stock.symbol} 
                className="search-result-item"
                onClick={() => selectStock(stock)}
              >
                <div className="result-symbol">{stock.symbol}</div>
                <div className="result-name">{stock.description}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Stock Detail or Empty State */}
      {selectedStock ? (
        renderStockDetail()
      ) : (
        <div className="empty-state">
          <div className="empty-icon">📈</div>
          <h2>Search for a stock</h2>
          <p>Enter a ticker symbol to get AI-powered predictions and analysis</p>
          <div className="popular-stocks">
            <span>Popular:</span>
            {['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'NVDA'].map((symbol) => (
              <button 
                key={symbol}
                className="popular-stock-btn"
                onClick={() => selectStock({ symbol })}
              >
                {symbol}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Watchlist */}
      {watchlist.length > 0 && (
        <div className="watchlist-section">
          <h3>⭐ Watchlist</h3>
          <div className="watchlist-grid">
            {watchlist.map((symbol) => (
              <div 
                key={symbol} 
                className="watchlist-item"
                onClick={() => selectStock({ symbol })}
              >
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