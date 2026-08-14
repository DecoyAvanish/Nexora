import React from 'react'
import './StatsRow.css'
import stockSVG from './stock.svg'

function StatsRow(props) {
    const per = ((props.price - props.openPrice) / props.openPrice) * 100;
    const isPositive = per >= 0;
 
    return (
        <div className="row">
            <div className="intro">
                <h1>{props.name}</h1>
                <p>{props.shares && (props.shares + " shares")}</p>
            </div>
            <div className="chart">
                <img src={stockSVG} height={16} alt="stock" />
            </div>
            <div className="num">
                <p className="price">${props.price?.toFixed(2)}</p>
                <p className={`per ${!isPositive ? 'negative' : ''}`}>
                    {isPositive ? '+' : ''}{per.toFixed(2)}%
                </p>
            </div>
        </div>
    )
}

export default StatsRow