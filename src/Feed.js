import React from 'react'
import './Feed.css'
import LineGraph from './LineGraph'
import TimeLine from './TimeLine'

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
            <TimeLine />
          </div>
        </div>
        <div className = "buying">
          <h2>Buying Power</h2>
          <h2>$4.11</h2>
        </div>
        <div className = "market">
          <div className = "box">
            <p>Markets Closed</p>
            <h1>Happy Thanksgiving</h1>
          </div>
        </div>
        <div className = "poplist">
          <div className = "intro">
            <h1>Popular lists</h1>
            <p>Sjow More</p>
          </div>
          <div className = "badges">
            {popularTopics.map((topic) => (
              <Chip
                className = "badge"
                variant = "outlined"
                label = {topic}
                avatar = {<Avatar src = {``}/>}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Feed
