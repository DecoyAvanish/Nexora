import React from 'react'
import './Feed.css'

function StockDisplay() {
  return (
    <div className = "feed">
      <div className = "container">
        <div className = "chart">
          <div className = "portfolio">
            <h1>$114,656</h1>
            <p>+44.63 (+0.04%) Today</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StockDisplay
