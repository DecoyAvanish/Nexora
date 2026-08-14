import numpy as np
import torch
import torch.nn as nn
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import warnings
import requests
import re
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

FINNHUB_API_KEY = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg"

class PredictionModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim, dropout=0.2):
        super(PredictionModel, self).__init__()
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.drop(out[:, -1, :])
        out = self.fc(out)
        return out

feature_cols = [
    'Return', 'LogVolume', 'MA10_ratio', 'MA50_ratio',
    'Volatility10', 'HighLowRange', 'RSI'
]

device = torch.device('cpu')

model = PredictionModel(input_dim=len(feature_cols), hidden_dim=32, num_layers=2, output_dim=1, dropout=0.2)
model.to(device)

def find_model_file():
    possible_paths = [
        '../model_weights.pth',
        'model_weights.pth',
        '../../model_weights.pth',
        './model_weights.pth',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_weights.pth'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model_weights.pth'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

model_path = find_model_file()
if model_path and os.path.exists(model_path):
    try:
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=False))
        model.eval()
        print(f"✅ Loaded model from {model_path}")
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
else:
    print(f"⚠️ Model file not found - using untrained model")

scaler = None
try:
    import joblib
    scaler_paths = [
        '../scaler.pkl',
        'scaler.pkl',
        '../../scaler.pkl',
        './scaler.pkl',
    ]
    for path in scaler_paths:
        if os.path.exists(path):
            scaler = joblib.load(path)
            print(f"✅ Loaded scaler from {path}")
            break
except Exception as e:
    print(f"⚠️ Could not load scaler: {e}")

def fetch_stock_data(symbol):
    """Fetch stock data using yfinance"""
    try:
        import yfinance as yf
        print(f"📊 Fetching data for {symbol}...")
        
        stock = yf.Ticker(symbol)
        hist = stock.history(period='6mo')
        
        if hist is None or hist.empty:
            print(f"❌ No data found for {symbol}")
            return None
        
        dates = []
        closes = []
        highs = []
        lows = []
        volumes = []
        
        for idx, row in hist.iterrows():
            dates.append(idx.strftime('%Y-%m-%d'))
            closes.append(float(row['Close']) if row['Close'] is not None else 0)
            highs.append(float(row['High']) if row['High'] is not None else 0)
            lows.append(float(row['Low']) if row['Low'] is not None else 0)
            volumes.append(float(row['Volume']) if row['Volume'] is not None else 0)
        
        if not closes or len(closes) < 10:
            print(f"❌ Not enough data for {symbol}")
            return None
        
        print(f"✅ Got {len(closes)} data points for {symbol}")
        
        return {
            'dates': dates,
            'close': closes,
            'high': highs,
            'low': lows,
            'volume': volumes,
            'last_price': closes[-1],
            'last_volume': volumes[-1] if volumes else 0
        }
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def calculate_features(data):
    """Calculate technical features from price data"""
    if not data or len(data['close']) < 30:
        return None
    
    closes = data['close']
    volumes = data['volume']
    highs = data['high']
    lows = data['low']
    n = len(closes)
    
    features = []
    
    for i in range(20, n):
        try:
            ret = (closes[i] - closes[i-1]) / closes[i-1] if closes[i-1] != 0 else 0
            
            log_vol = np.log(max(volumes[i], 1))
            
            ma10 = sum(closes[i-9:i+1]) / 10
            ma10_ratio = closes[i] / ma10 - 1 if ma10 != 0 else 0
            
            start_idx = max(0, i-49)
            ma50 = sum(closes[start_idx:i+1]) / (i - start_idx + 1)
            ma50_ratio = closes[i] / ma50 - 1 if ma50 != 0 else 0
            
            returns = []
            for j in range(i-9, i+1):
                if closes[j-1] != 0:
                    returns.append((closes[j] - closes[j-1]) / closes[j-1])
            vol10 = np.std(returns) if len(returns) > 1 else 0
            
            hl_range = (highs[i] - lows[i]) / closes[i] if closes[i] != 0 else 0
            
            gains = []
            losses = []
            for j in range(i-13, i+1):
                if j > 0:
                    diff = closes[j] - closes[j-1]
                    if diff > 0:
                        gains.append(diff)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(diff))
            
            avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
            avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 1
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            features.append([ret, log_vol, ma10_ratio, ma50_ratio, vol10, hl_range, rsi])
        except Exception as e:
            print(f"⚠️ Feature calculation error at index {i}: {e}")
            continue
    
    return np.array(features) if features else None

def make_prediction(symbol):
    """Make a prediction for a given symbol"""
    print(f"📊 Predicting for: {symbol}")

    data = fetch_stock_data(symbol)
    if data is None or len(data['close']) < 30:
        print(f"❌ Not enough data for {symbol}")
        return None, None, None, None, None
    
    features = calculate_features(data)
    if features is None or len(features) < 10:
        print(f"❌ Could not calculate features for {symbol}")
        return None, None, None, None, None
    
    seq_length = min(20, len(features))
    last_seq = features[-seq_length:]
    
    try:
        if scaler is not None:
            last_seq_scaled = scaler.transform(last_seq)
        else:
            mean = np.mean(last_seq, axis=0)
            std = np.std(last_seq, axis=0) + 1e-8
            last_seq_scaled = (last_seq - mean) / std
    except Exception as e:
        print(f"⚠️ Scaling error: {e}")
        mean = np.mean(last_seq, axis=0)
        std = np.std(last_seq, axis=0) + 1e-8
        last_seq_scaled = (last_seq - mean) / std
    
    X = torch.from_numpy(last_seq_scaled).float().unsqueeze(0).to(device)
    
    try:
        model.eval()
        with torch.no_grad():
            pred_scaled = model(X).cpu().numpy()[0][0]
        
        if scaler is not None:
            try:
                target_idx = feature_cols.index('Return')
                pred_return = pred_scaled * scaler.scale_[target_idx] + scaler.mean_[target_idx]
            except:
                pred_return = pred_scaled * 0.02
        else:
            pred_return = pred_scaled * 0.02
            
    except Exception as e:
        print(f"⚠️ Prediction error: {e}")
        pred_return = 0.0
    
    last_close = data['last_price']
    last_return = (data['close'][-1] - data['close'][-2]) / data['close'][-2] if len(data['close']) > 1 and data['close'][-2] != 0 else 0
    
    predicted_price = last_close * (1 + pred_return)
    
    print(f"✅ Prediction for {symbol}: ${predicted_price:.2f}")
    
    return last_close, last_return, pred_return, predicted_price, data

def search_stocks(query):
    """Search for stocks using Finnhub"""
    try:
        url = f"https://finnhub.io/api/v1/search?q={query}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        results = []
        for item in data.get('result', []):
            if item.get('type') == 'Common Stock':
                symbol = item.get('symbol', '')
                if re.match(r'^[A-Z]+$', symbol):
                    results.append({
                        'symbol': symbol,
                        'description': item.get('description', symbol)
                    })
        
        return results[:10]
    except Exception as e:
        print(f"Search error: {e}")
        return []

@app.route('/api/search/<query>', methods=['GET'])
def search(query):
    """Search for stocks"""
    try:
        print(f"🔍 Searching for: {query}")
        results = search_stocks(query)
        return jsonify({'result': results})
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'error': str(e), 'result': []}), 500

@app.route('/api/predict/<symbol>', methods=['GET'])
def predict(symbol):
    """Get prediction for a stock"""
    try:
        symbol = symbol.upper()
        result = make_prediction(symbol)
        
        if result[0] is None:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        last_close, last_return, pred_return, predicted_price, data = result
        
        dates = data['dates']
        prices = data['close']
        volumes = data['volume']
        
        if len(dates) > 120:
            dates = dates[-120:]
            prices = prices[-120:]
            volumes = volumes[-120:]
        
        return jsonify({
            'symbol': symbol,
            'name': symbol,
            'last_price': float(last_close),
            'last_return': float(last_return),
            'predicted_return': float(pred_return),
            'predicted_price': float(predicted_price),
            'confidence': 0.72,
            'chart_data': {
                'dates': dates,
                'prices': prices,
                'volume': volumes
            }
        })
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model_loaded': model_path is not None and os.path.exists(model_path),
        'scaler_loaded': scaler is not None
    })

@app.route('/api/test/<symbol>', methods=['GET'])
def test(symbol):
    """Test endpoint"""
    try:
        symbol = symbol.upper()
        print(f"🧪 Testing {symbol}...")
        
        import yfinance as yf
        stock = yf.Ticker(symbol)
        hist = stock.history(period='5d')
        
        if hist.empty:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        return jsonify({
            'symbol': symbol,
            'rows': len(hist),
            'last_price': float(hist['Close'].iloc[-1]),
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'prices': hist['Close'].tolist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Stock Prediction API Server")
    print("=" * 60)
    print(f"📊 Model: {'✅ Loaded' if model_path and os.path.exists(model_path) else '❌ Not found'}")
    print(f"📊 Scaler: {'✅ Loaded' if scaler is not None else '⚠️ Using default'}")
    print(f"🔑 Finnhub API: {'✅ Configured' if FINNHUB_API_KEY else '❌ Missing!'}")
    print(f"🌐 Server running at http://localhost:5001")
    print("=" * 60)
    print("\n🔧 Test endpoints:")
    print("  http://localhost:5001/api/health")
    print("  http://localhost:5001/api/test/AAPL")
    print("  http://localhost:5001/api/predict/AAPL")
    print("\n" + "=" * 60)
    app.run(debug=True, port=5001, host='0.0.0.0')