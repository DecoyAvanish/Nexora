import React from 'react'
import './StatsRow.css'
import stockSVG from './stock.svg'

function StatsRow(props) {

    const per = ((props.price - props.openPrice)/props.openPrice) * 100;
 
    return (
        <div className = "row">
            <div className = "intro">
                <h1>{props.name}</h1>
                <p>{props.shares && (props.shares + "shares")}</p>
            </div>
            <div className = "chart">
                <img src = {stockSVG} height = {16}/>
            </div>
            <div className = "num">
                <p className = "price">{props.price}</p>
                <p className = "per">{Number(per).toFixed(2)}%</p>
            </div>
        </div>
    )
}

export default StatsRow
