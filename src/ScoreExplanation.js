import React from 'react';
import './ScoreExplanation.css';

const pretty=(value)=>value?.replaceAll('_',' ') || '';
export default function ScoreExplanation({data}){
  if(!data)return null;
  const waterfall=data.shap.waterfall||[]; const max=Math.max(...waterfall.map(item=>Math.abs(item.value)),.001);
  const history=data.score_history||[]; const points=history.map((item,index)=>`${history.length===1?50:index/(history.length-1)*100},${100-(item.score-1)/9*100}`).join(' ');
  return <section className="why-score">
    <header><div><span>MODEL EXPLAINABILITY</span><h2>Why this score?</h2></div><strong>{data.score.ai_score}/10</strong></header>
    <div className="explain-insights">{data.summary.insights.map(text=><p key={text}>{text}</p>)}</div>
    <div className="contribution-grid">{Object.entries(data.contributions).map(([name,item])=><article key={name} className={!item.included_in_model?'context-only':''}><span>{name}</span><strong>{(item.share_of_absolute_impact*100).toFixed(0)}%</strong><small>{item.included_in_model?'model impact':'context only'}</small></article>)}</div>
    <div className="explain-columns"><div><h3>Top positive drivers</h3>{data.drivers.positive.map(driver=><div className="driver-row positive" key={driver.feature}><span>{driver.label}</span><b>+{driver.value.toFixed(3)}</b><small>{driver.scope==='sector_relative'?'Sector relative':'Universe relative'}</small></div>)}</div><div><h3>Top negative drivers</h3>{data.drivers.negative.map(driver=><div className="driver-row negative" key={driver.feature}><span>{driver.label}</span><b>{driver.value.toFixed(3)}</b><small>{driver.scope==='sector_relative'?'Sector relative':'Universe relative'}</small></div>)}</div></div>
    <div className="explain-panels"><div className="waterfall"><h3>SHAP waterfall</h3><p>Directional raw model-margin contributions</p>{waterfall.map(item=><div className="waterfall-row" key={item.feature}><label title={item.label}>{item.label}</label><div><i className={item.direction} style={{width:`${Math.max(4,Math.abs(item.value)/max*100)}%`}} /></div><b>{item.value>0?'+':''}{item.value.toFixed(3)}</b></div>)}</div>
    <div className="score-history"><h3>Score change history</h3>{history.length>1?<><svg viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points={points} /></svg><div><span>{history[0].score}/10</span><span>{history.at(-1).score}/10</span></div></>:<p>History starts after multiple score observations.</p>}</div></div>
    <div className="news-evidence"><h3>News intelligence</h3><div><article><span>Sentiment</span><strong>{data.summary.news.label}</strong></article><article><span>Confidence</span><strong>{data.summary.news.confidence?.level||'Low'}</strong></article><article><span>Coverage</span><strong>{data.summary.news.coverage||0}</strong></article><article><span>Novel events</span><strong>{data.summary.news.novel_events||0}</strong></article><article><span>Source agreement</span><strong>{data.summary.news.source_agreement!=null?`${(data.summary.news.source_agreement*100).toFixed(0)}%`:'N/A'}</strong></article><article><span>Primary theme</span><strong>{data.summary.news.primary_theme||'N/A'}</strong></article></div></div>
    <div className="sector-freshness"><div><h3>Sector-relative comparison</h3><strong>{data.sector_comparison.sector_percentile?.toFixed(0)}th percentile</strong><p>{data.sector_comparison.sector} · {data.sector_comparison.universe_percentile?.toFixed(0)}th universe percentile</p></div><div><h3>Data freshness</h3>{Object.entries(data.data_freshness).map(([name,value])=><p key={name}><span>{pretty(name)}</span><b>{value||'Unavailable'}</b></p>)}</div></div>
    {data.missing_data_warnings.length>0&&<div className="data-warnings"><h3>Data-quality warnings</h3>{data.missing_data_warnings.map(warning=><p key={warning}>⚠ {warning}</p>)}</div>}
    <div className="explain-sources"><h3>Evidence sources</h3>{data.sources.map(source=><a href={source.url} target="_blank" rel="noreferrer" key={source.url}><span>{source.type}</span>{source.label} ↗</a>)}</div>
    <details className="limitations"><summary>Model limitations</summary>{data.model_limitations.map(item=><p key={item}>{item}</p>)}</details>
  </section>;
}
