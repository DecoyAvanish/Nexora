import React from 'react'
import './Stats.css'

function Stats() {
  return (
    <div className = "stats">
      <div className = "container">
        <div className = "header">
          <p>Stocks</p>
        </div>
        <div className = "content">
          <div className = "rows">
            {/*stocks we have*/}
          </div>
        </div>
        <div className = "header">
          <p>Lists</p>
        </div>
        <div className = "content">
          <div className = "rows">
            {/*stocks we can buy*/}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Stats
