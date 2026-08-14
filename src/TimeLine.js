import React from 'react'
import './TimeLine.css'

function TimeLine() {
  const timeframes = ['LIVE', '1D', '1W', '1M', '3M', '1Y', 'ALL'];
  
  return (
    <div className="timelinecontainer">
      <div className="buttonscontainer">
        {timeframes.map((tf) => (
          <div key={tf} className={`button ${tf === '1W' ? 'active' : ''}`}>
            {tf}
          </div>
        ))}
      </div>
    </div>
  )
}

export default TimeLine