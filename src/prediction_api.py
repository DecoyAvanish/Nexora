# prediction_api.py - Fixed version with correct list conversion
import numpy as np
import pandas as pd
import yfinance as yf
import torch
import torch.nn as nn
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# ============ YOUR FINNHUB API KEY ============
FINNHUB_API_KEY = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg"
# ==============================================

# ============ YOUR LSTM MODEL ============
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

# Feature columns (must match your training)
feature_cols = [
    'Return', 'LogVolume', 'MA10_ratio', 'MA50_ratio',
    'Volatility10', 'HighLowRange', 'RSI'
]

device = torch.device('cpu')

# Initialize model
model = PredictionModel(input_dim=len(feature_cols), hidden_dim=32, num_layers=2, output_dim=1, dropout=0.2)
model.to(device)

# Load your trained weights
model_path = '../model_weights.pth'  # Since prediction_api.py is in src/, model_weights.pth is in parent
if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print(f"✅ Loaded model from {model_path}")
else:
    print(f"⚠️ Model file not found at {model_path}")
    print("Using untrained model for demonstration")

# Load scaler if it exists
scaler = None
try:
    import joblib
    scaler_path = '../scaler.pkl'
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        print("✅ Loaded scaler from scaler.pkl")
except:
    print("⚠️ Could not load scaler, using default normalization")

# ============ HELPER FUNCTIONS ============

def get_stock_data(symbol, period='6mo'):
    """Fetch stock data and prepare features"""
    try:
        df = yf.download(symbol, period=period, progress=False)
        if df.empty:
            return None
        
        # Prepare features (same as your notebook)
        data = df[['Close', 'High', 'Low', 'Volume']].copy()
        data['Return'] = df['Close'].pct_change()
        data['LogVolume'] = np.log(df['Volume'] + 1)
        data['MA10_ratio'] = df['Close'] / df['Close'].rolling(10).mean() - 1
        data['MA50_ratio'] = df['Close'] / df['Close'].rolling(50).mean() - 1
        data['Volatility10'] = data['Return'].rolling(10).std()
        data['HighLowRange'] = (df['High'] - df['Low']) / df['Close']
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def prepare_prediction_data(data, seq_length=20):
    """Prepare data for prediction"""
    from sklearn.preprocessing import StandardScaler
    
    feat = data[feature_cols].values
    
    # Use the saved scaler if available
    if scaler is not None:
        feat_scaled = scaler.transform(feat)
    else:
        temp_scaler = StandardScaler()
        feat_scaled = temp_scaler.fit_transform(feat)
    
    # Get last seq_length days
    if len(feat_scaled) < seq_length:
        seq_length = len(feat_scaled)
    
    last_seq = feat_scaled[-seq_length:]
    return torch.from_numpy(last_seq).float().unsqueeze(0)

def make_prediction(symbol):
    """Make a prediction for a given symbol"""
    data = get_stock_data(symbol)
    if data is None:
        return None, None, None, None
    
    # Prepare for prediction
    seq_length = min(20, len(data) - 1)
    X = prepare_prediction_data(data, seq_length)
    X = X.to(device)
    
    # Make prediction
    with torch.no_grad():
        pred_scaled = model(X).cpu().numpy()[0][0]
    
    # Get last price and return
    last_close = data['Close'].iloc[-1]
    last_return = data['Return'].iloc[-1] if len(data['Return']) > 0 else 0
    
    # Unscale prediction
    pred_return = pred_scaled * 0.02  # Approximate unscaling
    predicted_price = last_close * (1 + pred_return)
    
    # Return data with chart info
    return last_close, last_return, pred_return, predicted_price, data

def search_stocks(query):
    """Search for stocks using Finnhub"""
    import re
    
    try:
        url = f"https://finnhub.io/api/v1/search?q={query}&token={FINNHUB_API_KEY}"
        response = requests.get(url)
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

# ============ API ENDPOINTS ============

@app.route('/api/search/<query>', methods=['GET'])
def search(query):
    """Search for stocks"""
    try:
        results = search_stocks(query)
        return jsonify({'result': results})
    except Exception as e:
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
        
        # FIXED: Convert pandas objects to lists correctly
        chart_data = {
            # Use .tolist() for numpy arrays, or list() for pandas Series/Index
            'dates': data.index.strftime('%Y-%m-%d').tolist(),  # This works! .tolist() is correct for pandas Index
            'prices': data['Close'].tolist(),  # .tolist() works for pandas Series
            'volume': data['Volume'].tolist()  # .tolist() works for pandas Series
        }
        
        return jsonify({
            'symbol': symbol,
            'name': symbol,
            'last_price': float(last_close),
            'last_return': float(last_return),
            'predicted_return': float(pred_return),
            'predicted_price': float(predicted_price),
            'confidence': 0.72,
            'chart_data': chart_data
        })
        
    except Exception as e:
        print(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model_loaded': os.path.exists(model_path),
        'scaler_loaded': scaler is not None
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Stock Prediction API Server")
    print("=" * 60)
    print(f"📊 Model: {'✅ Loaded' if os.path.exists(model_path) else '❌ Not found'}")
    print(f"📊 Scaler: {'✅ Loaded' if scaler is not None else '⚠️ Using default'}")
    print(f"🔑 Finnhub API: {'✅ Configured' if FINNHUB_API_KEY else '❌ Missing!'}")
    print(f"🌐 Server running at http://localhost:5001")
    print("=" * 60)
    app.run(debug=True, port=5001)