import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import './StatsRow.css';

const FINNHUB_TOKEN = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg";
const CACHE = {};

function StatsRow(props) {
  const currentPrice = props.price || 0;
  const previousClose = props.previousClose || props.openPrice || currentPrice;
  
  const per = previousClose > 0 ? ((currentPrice - previousClose) / previousClose) * 100 : 0;
  const isPositive = per >= 0;
  
  const canvasRef = useRef(null);
  const [sparklineData, setSparklineData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistoricalData = async () => {
      if (!props.name) return;
      
      if (CACHE[props.name]) {
        setSparklineData(CACHE[props.name]);
        setLoading(false);
        return;
      }

      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        const from = Math.floor(startDate.getTime() / 1000);
        const to = Math.floor(endDate.getTime() / 1000);
        
        const response = await axios.get(
          `https://finnhub.io/api/v1/stock/candle?symbol=${props.name}&resolution=D&from=${from}&to=${to}&token=${FINNHUB_TOKEN}`
        );
        
        if (response.data && response.data.c && response.data.c.length > 0) {
          let data = response.data.c;
          if (data.length > 0 && currentPrice > 0) {
            data[data.length - 1] = currentPrice;
          }
          CACHE[props.name] = data;
          setSparklineData(data);
        } else {
          const mockData = generateMockData();
          CACHE[props.name] = mockData;
          setSparklineData(mockData);
        }
      } catch (error) {
        console.error(`Error fetching data for ${props.name}:`, error);
        const mockData = generateMockData();
        CACHE[props.name] = mockData;
        setSparklineData(mockData);
      } finally {
        setLoading(false);
      }
    };

    const generateMockData = () => {
      const data = [];
      let val = previousClose || 100;
      const steps = 30;
      const targetEnd = currentPrice || val;
      
      for (let i = 0; i < steps; i++) {
        const progress = i / steps;
        const noise = (Math.random() - 0.5) * 3;
        const trend = (targetEnd - val) * progress;
        const current = val + trend + noise * (1 - progress * 0.8);
        data.push(Math.max(current, 0.1));
      }
      if (data.length > 0) {
        data[data.length - 1] = targetEnd;
      }
      return data;
    };

    fetchHistoricalData();
  }, [props.name, currentPrice, previousClose]);

  useEffect(() => {
    if (!canvasRef.current || loading || !sparklineData || sparklineData.length < 2) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    ctx.scale(dpr, dpr);
    
    const data = sparklineData;
    const width = rect.width;
    const height = rect.height;
    const padding = 2;
    const graphWidth = width - padding * 2;
    const graphHeight = height - padding * 2;
    
    const lineColor = isPositive ? '#A855F7' : '#ff6b5e';
    
    const min = Math.min(...data) * 0.98;
    const max = Math.max(...data) * 1.02;
    const range = max - min || 1;
    
    ctx.clearRect(0, 0, width, height);
    
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    if (isPositive) {
      gradient.addColorStop(0, 'rgba(168, 85, 247, 0.2)');
      gradient.addColorStop(1, 'rgba(168, 85, 247, 0)');
    } else {
      gradient.addColorStop(0, 'rgba(255, 107, 94, 0.2)');
      gradient.addColorStop(1, 'rgba(255, 107, 94, 0)');
    }
    
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    data.forEach((val, i) => {
      const x = padding + (i / (data.length - 1)) * graphWidth;
      const y = padding + (1 - (val - min) / range) * graphHeight;
      if (i === 0) ctx.lineTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(padding + graphWidth, height - padding);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    
    ctx.beginPath();
    data.forEach((val, i) => {
      const x = padding + (i / (data.length - 1)) * graphWidth;
      const y = padding + (1 - (val - min) / range) * graphHeight;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    const lastX = padding + graphWidth;
    const lastY = padding + (1 - (data[data.length - 1] - min) / range) * graphHeight;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = lineColor;
    ctx.fill();
    ctx.strokeStyle = '#080a11';
    ctx.lineWidth = 1;
    ctx.stroke();
    
  }, [sparklineData, loading, isPositive]);

  return (
    <div className="row">
      <div className="intro">
        <h1>{props.name}</h1>
        <p>{props.shares > 0 ? props.shares + ' shares' : '—'}</p>
      </div>
      <div className="sparkline">
        <canvas ref={canvasRef} />
      </div>
      <div className="num">
        <p className="price">${currentPrice.toFixed(2)}</p>
        <p className={`per ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '+' : ''}{per.toFixed(2)}%
        </p>
      </div>
    </div>
  );
}

export default StatsRow;