import React, { useEffect, useMemo, useState } from 'react';
import 'chart.js/auto';
import { Bar, Line, Scatter } from 'react-chartjs-2';
import './ModelLab.css';
import './EvaluationMetrics.css';
import './EvaluationHeader.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL || '/api';
const pct = (value, digits = 1) => value == null ? 'N/A' : `${(value * 100).toFixed(digits)}%`;
const number = (value, digits = 3) => value == null ? 'N/A' : Number(value).toFixed(digits);
const strategyLabel = (name) => ({
  cross_sectional_model: 'Nexora AI',
  buy_and_hold_spy: 'Buy & Hold SPY',
  simple_momentum: 'Simple Momentum',
  random_selection: 'Random Selection',
  technical_only: 'Technical Only',
  sentiment_only: 'Sentiment Only',
}[name] || name);

function MetricCard({ label, value, detail, tone = 'purple' }) {
  return <div className={`lab-metric ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function ModelLab() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/model-lab`)
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.error?.message || 'Model evaluation is unavailable.');
        return body;
      })
      .then(setReport)
      .catch(err => setError(err.message));
  }, []);

  const equityChart = useMemo(() => {
    if (!report) return null;
    const colors = ['#a855f7', '#38bdf8', '#4bff9b', '#f59e0b', '#fb7185'];
    const datasets = Object.entries(report.performance)
      .filter(([, result]) => result.available && result.period_returns)
      .map(([name, result], index) => {
        let wealth = 1;
        return {
          label: strategyLabel(name),
          data: result.period_returns.map(point => ({ x: point.date, y: (wealth *= 1 + point.net) - 1 })),
          borderColor: colors[index % colors.length],
          backgroundColor: 'transparent',
          tension: 0.25,
          pointRadius: 2,
        };
      });
    return { datasets };
  }, [report]);

  if (error) return <main className="model-lab"><div className="lab-state"><h1>Model Lab unavailable</h1><p>{error}</p></div></main>;
  if (!report) return <main className="model-lab"><div className="lab-state"><div className="loading-spinner"></div><p>Loading walk-forward evidence…</p></div></main>;

  const wf = report.walk_forward;
  const model = report.performance.cross_sectional_model;
  const calibrationData = {
    datasets: [
      { label: 'Observed', data: report.calibration_curve.map(p => ({ x: p.predicted_probability, y: p.observed_frequency })), backgroundColor: '#a855f7', pointRadius: 6 },
      { label: 'Perfect calibration', data: [{ x: 0, y: 0 }, { x: 1, y: 1 }], borderColor: 'rgba(255,255,255,.25)', borderDash: [5, 5], showLine: true, pointRadius: 0 },
    ],
  };
  const foldChart = {
    labels: wf.fold_metrics.map((fold, index) => `F${index + 1}`),
    datasets: [
      { label: 'Nexora AI AUC', data: wf.fold_metrics.map(fold => fold.model_auc), backgroundColor: '#a855f7' },
      { label: 'Momentum AUC', data: wf.fold_metrics.map(fold => fold.momentum_auc), backgroundColor: '#38bdf8' },
    ],
  };

  return (
    <main className="model-lab">
      <section className="lab-hero">
        <div><p className="lab-kicker">PUBLIC MODEL TRANSPARENCY</p><h1>MODEL <span>LAB</span></h1><p>Out-of-sample evidence, costs, failures, and limitations. No cherry-picked backtest.</p></div>
        <div className="lab-version"><span>MODEL</span><strong>{report.model_version}</strong><span>DATA THROUGH</span><strong>{report.data_through}</strong></div>
      </section>

      <section className="lab-metrics-grid">
        <MetricCard label="Walk-forward AUC" value={number(wf.mean_auc)} detail={`${wf.folds} purged folds`} />
        <MetricCard label="Information coefficient" value={number(wf.mean_information_coefficient)} detail="Spearman rank correlation" tone="blue" />
        <MetricCard label="Top-bottom spread" value={pct(wf.mean_top_bottom_decile_spread)} detail="Average 63-day excess spread" tone="green" />
        <MetricCard label="Net cumulative return" value={pct(model.transaction_cost_adjusted_return)} detail={`${model.transaction_cost_bps} bps cost assumption`} tone="green" />
        <MetricCard label="Maximum drawdown" value={pct(model.maximum_drawdown)} detail="Cost-adjusted long-short" tone="red" />
        <MetricCard label="Sharpe / Sortino" value={`${number(model.sharpe_ratio, 2)} / ${number(model.sortino_ratio, 2)}`} detail="Quarterly rebalance series" tone="blue" />
        <MetricCard label="Average turnover" value={pct(model.average_turnover)} detail="One-way decile turnover" tone="amber" />
        <MetricCard label="Gross cumulative return" value={pct(model.gross_cumulative_return)} detail={`${model.periods} non-overlapping periods`} />
      </section>

      <section className="lab-panel lab-wide"><div className="lab-panel-title"><div><span>01</span><h2>Cumulative long-short performance</h2></div><p>Net of configured transaction costs</p></div><div className="lab-chart tall">{equityChart && <Line data={equityChart} options={{ parsing: false, responsive: true, maintainAspectRatio: false, scales: { x: { type: 'time', time: { unit: 'year' } }, y: { ticks: { callback: value => `${(value * 100).toFixed(0)}%` } } } }} />}</div></section>

      <div className="lab-two-column">
        <section className="lab-panel"><div className="lab-panel-title"><div><span>02</span><h2>Fold stability</h2></div></div><div className="lab-chart"><Bar data={foldChart} options={{ responsive: true, maintainAspectRatio: false, scales: { y: { min: 0.35, max: 0.7 } } }} /></div></section>
        <section className="lab-panel"><div className="lab-panel-title"><div><span>03</span><h2>Calibration curve</h2></div></div><div className="lab-chart"><Scatter data={calibrationData} options={{ responsive: true, maintainAspectRatio: false, scales: { x: { min: 0, max: 1, title: { display: true, text: 'Predicted probability' } }, y: { min: 0, max: 1, title: { display: true, text: 'Observed frequency' } } } }} /></div></section>
      </div>

      <section className="lab-panel"><div className="lab-panel-title"><div><span>04</span><h2>Baseline comparison</h2></div><p>Unavailable means unavailable—not zero</p></div><div className="baseline-grid">{Object.entries(report.baseline_comparison).map(([name, result]) => <div className="baseline-row" key={name}><strong>{strategyLabel(name)}</strong><span className={result.available ? 'available' : 'unavailable'}>{result.auc == null ? (result.available ? 'Return benchmark' : 'Insufficient history') : `AUC ${result.auc.toFixed(3)}`}</span></div>)}</div></section>

      <section className="lab-panel"><div className="lab-panel-title"><div><span>05</span><h2>Performance by market regime</h2></div></div><div className="regime-grid">{Object.entries(report.market_regimes).map(([name, regime]) => <div className={`regime-card ${name}`} key={name}><span>{name.toUpperCase()}</span><strong>{pct(regime.cumulative_long_short_return)}</strong><small>{regime.periods} periods • avg {pct(regime.average_long_short_return)}</small></div>)}</div></section>

      <section className="lab-panel"><div className="lab-panel-title"><div><span>06</span><h2>Feature-importance stability</h2></div></div>{report.feature_importance_stability.available ? <><p className="stability-score">Consecutive-fold rank correlation: <strong>{number(report.feature_importance_stability.mean_consecutive_fold_rank_correlation)}</strong></p><div className="feature-list">{report.feature_importance_stability.top_features.map(feature => <div key={feature.feature}><span>{feature.feature.replaceAll('_', ' ')}</span><strong>{number(feature.mean_importance, 1)}</strong></div>)}</div></> : <div className="lab-unavailable">{report.feature_importance_stability.reason}</div>}</section>

      <section className="lab-limitations"><h2>Methodology & limitations</h2><div><span>63-day embargo</span><span>Platt calibrated</span><span>10 bps costs</span><span>{report.universe}</span></div><ul>{report.methodology.limitations.map(item => <li key={item}>{item}</li>)}</ul></section>
    </main>
  );
}

export default ModelLab;
