// StatsRow.js - Updated with sparkline charts
import React, { useEffect, useRef } from 'react';
import './StatsRow.css';

function StatsRow(props) {
  const per = ((props.price - props.openPrice) / props.openPrice) * 100;
  const isPositive = per >= 0;
  const canvasRef = useRef(null);

  // Generate mock sparkline data for each stock
  const generateSparklineData = () => {
    const data = [];
    let val = props.openPrice || 100;
    const steps = 30;
    
    for (let i = 0; i < steps; i++) {
      const change = (Math.random() - 0.48) * 5;
      val = Math.max(val + change, val * 0.7);
      data.push(val);
    }
    // Make sure last value matches current price
    data[data.length - 1] = props.price || val;
    return data;
  };

  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    ctx.scale(dpr, dpr);
    
    const data = generateSparklineData();
    const width = rect.width;
    const height = rect.height;
    const padding = 2;
    const graphWidth = width - padding * 2;
    const graphHeight = height - padding * 2;
    
    const min = Math.min(...data) * 0.98;
    const max = Math.max(...data) * 1.02;
    const range = max - min || 1;
    
    ctx.clearRect(0, 0, width, height);
    
    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    if (isPositive) {
      gradient.addColorStop(0, 'rgba(168, 85, 247, 0.15)');
      gradient.addColorStop(1, 'rgba(168, 85, 247, 0)');
    } else {
      gradient.addColorStop(0, 'rgba(255, 107, 94, 0.15)');
      gradient.addColorStop(1, 'rgba(255, 107, 94, 0)');
    }
    
    // Draw fill
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
    
    // Draw line
    ctx.beginPath();
    data.forEach((val, i) => {
      const x = padding + (i / (data.length - 1)) * graphWidth;
      const y = padding + (1 - (val - min) / range) * graphHeight;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = isPositive ? '#A855F7' : '#ff6b5e';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    const lastX = padding + graphWidth;
    const lastY = padding + (1 - (data[data.length - 1] - min) / range) * graphHeight;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = isPositive ? '#A855F7' : '#ff6b5e';
    ctx.fill();
    ctx.strokeStyle = '#080a11';
    ctx.lineWidth = 1;
    ctx.stroke();
    
  }, [props.price, props.openPrice]);

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
        <p className="price">${props.price?.toFixed(2) || '0.00'}</p>
        <p className={`per ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '+' : ''}{per.toFixed(2)}%
        </p>
      </div>
    </div>
  );
}

export default StatsRow;