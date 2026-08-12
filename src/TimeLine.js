import React from 'react'
import './TimeLine.css'

function TimeLine() {
    return (
        <div className = "timelinecontainer">
            <div className = "buttonscontainer">
                <div className = "button">LIVE</div>
                <div className = "button">1D</div>
                <div className = "button active">1W</div>
                <div className = "button">3M</div>
                <div className = "button">1Y</div>
                <div className = "button">ALL</div>
            </div>
        </div>
    )
}

export default TimeLine
