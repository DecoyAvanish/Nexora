import React from 'react'
import './Feed.css'
import LineGraph from './LineGraph'
import TimeLine from './TimeLine'
import Chip from './Chip'

const popularTopics = [
  { name: "Technology", icon: "💻" },
  { name: "Top Movies", icon: "🎬" },
  { name: "Upcoming Earnings", icon: "📈" },
  { name: "Cryptocurrency", icon: "₿" },
  { name: "Cannabis", icon: "🌿" },
  { name: "Healthcare Supplies", icon: "🏥" },
  { name: "Index ETFs", icon: "📊" },
  { name: "China", icon: "🇨🇳" },
  { name: "Pharmacy", icon: "💊" }
];

function Feed() {
  return (
    <div className="feed">
      <div className="container">
        <div className="chartsection">
          <div className="portfolio">
            <h1>$114,656</h1>
            <p><span className="positive">+44.63 (+0.04%)</span> Today</p>
          </div>
          <div className="chart-wrapper">
            <div className="chart">
              <LineGraph />
            </div>
            <div className="timeline-wrapper">
              <TimeLine />
            </div>
          </div>
        </div>
        <div className="buying">
          <h2>Buying Power</h2>
          <h2>$4.11</h2>
        </div>
        <div className="market">
          <div className="box">
            <p>Markets Closed</p>
            <h1>Happy Thanksgiving</h1>
          </div>
        </div>
        <div className="poplist">
          <div className="intro">
            <h1>Popular lists</h1>
            <p>Show More →</p>
          </div>
          <div className="badges">
            {popularTopics.map((topic) => (
              <Chip 
                key={topic.name}
                label={topic.name}
                icon={topic.icon}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Feed