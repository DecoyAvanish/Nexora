import React from 'react'
import './Feed.css'
import LineGraph from './LineGraph'

function Feed() {
  return (
    <div className = "feed">
      <div className = "container">
        <div className = "chartsection">
          <div className = "portfolio">
            <h1>$114,656</h1>
            <p>+44.63 (+0.04%) Today</p>
          </div>
          <div className = "chart">
            <LineGraph />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Feed
