import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { auth } from './firebase';
import './RiskLab.css';

const API_BASE=process.env.REACT_APP_API_BASE_URL || '/api';
const percent=(value)=>`${(value*100).toFixed(1)}%`;

export default function RiskLab(){
  const [data,setData]=useState(null); const [error,setError]=useState('');
  useEffect(()=>{(async()=>{try{const currentUser=auth.currentUser;const token=currentUser?await currentUser.getIdToken():null;const endpoint=currentUser?'risk/portfolio':'risk/demo';const response=await axios.get(`${API_BASE}/${endpoint}`,{headers:token?{Authorization:`Bearer ${token}`}:{},timeout:90000}); setData(response.data);}catch(err){setError(err.response?.data?.error?.message||'Risk analytics are unavailable.');}})();},[]);
  if(error)return <main className="risk-page"><div className="risk-empty">{error}</div></main>;
  if(!data)return <main className="risk-page"><div className="risk-empty">Running portfolio simulations…</div></main>;
  if(data.status==='empty')return <main className="risk-page"><div className="risk-empty">{data.message}</div></main>;
  const m=data.metrics;
  return <main className="risk-page">
    <header><span>PORTFOLIO RISK ENGINE</span><h1>Risk, factors & stress lab</h1><p>Fill-derived positions · data through {data.as_of} · paper trading only</p></header>
    {data.warnings.map((warning)=><div className="risk-warning" key={warning.title}><strong>{warning.title}</strong><span>{warning.message}</span></div>)}
    <section className="risk-metrics">{[['Beta vs SPY',m.beta_vs_spy],['Annual volatility',percent(m.annualized_volatility)],['Sharpe',m.sharpe],['Sortino',m.sortino],['95% daily VaR',percent(m.var_95_daily)],['Expected shortfall',percent(m.expected_shortfall_95)],['Max drawdown',percent(m.maximum_drawdown)],['Diversification',`${m.diversification_score}/100`]].map(([label,value])=><article key={label}><small>{label}</small><strong>{value}</strong></article>)}</section>
    <div className="risk-grid"><section><h2>Sector exposure</h2>{Object.entries(data.sector_exposure).sort((a,b)=>b[1]-a[1]).map(([sector,value])=><div className="risk-bar" key={sector}><label><span>{sector}</span><b>{percent(value)}</b></label><i style={{width:percent(value)}} /></div>)}</section>
    <section><h2>Monte Carlo · {data.monte_carlo.horizon_days} days</h2><div className="simulation"><div><small>Bear case (5th)</small><strong>{percent(data.monte_carlo.p05_return)}</strong></div><div><small>Median</small><strong>{percent(data.monte_carlo.median_return)}</strong></div><div><small>Bull case (95th)</small><strong>{percent(data.monte_carlo.p95_return)}</strong></div><p>{data.monte_carlo.simulations.toLocaleString()} paths · {percent(data.monte_carlo.probability_of_loss)} probability of loss</p></div></section></div>
    <section className="stress"><h2>Institutional stress scenarios</h2>{data.stress_tests.map(item=><div key={item.scenario}><span>{item.scenario}</span><strong className={item.estimated_return<0?'loss':'gain'}>{percent(item.estimated_return)}</strong></div>)}</section>
    <section className="correlation"><h2>Correlation matrix</h2><table><thead><tr><th></th>{data.correlation.symbols.map(s=><th key={s}>{s}</th>)}</tr></thead><tbody>{data.correlation.symbols.map((symbol,row)=><tr key={symbol}><th>{symbol}</th>{data.correlation.matrix[row].map((value,column)=><td key={column} style={{background:`rgba(168,85,247,${Math.abs(value)*.28})`}}>{value.toFixed(2)}</td>)}</tr>)}</tbody></table></section>
  </main>;
}
