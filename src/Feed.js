import React, { useState, useEffect } from 'react'
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
  const [marketStatus, setMarketStatus] = useState({
    isOpen: false,
    status: 'CLOSED',
    message: 'Weekend Retreat',
    timeLeft: ''
  });

  const [currentTime, setCurrentTime] = useState('');

  const getMarketStatus = () => {
    const now = new Date();
    const day = now.getDay();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();
    const currentTime = hours + minutes / 60 + seconds / 3600;

    const marketOpen = 9.5;
    const marketClose = 16;

    const isWeekday = day >= 1 && day <= 5;
    const isWithinHours = currentTime >= marketOpen && currentTime < marketClose;

    const holidays = [
      '01-01', '01-20', '02-17', '04-18', '05-26',
      '07-04', '09-01', '11-27', '12-25'
    ];

    const month = String(now.getMonth() + 1).padStart(2, '0');
    const date = String(now.getDate()).padStart(2, '0');
    const todayStr = `${month}-${date}`;
    const isHoliday = holidays.includes(todayStr);

    const isPreMarket = currentTime >= 4 && currentTime < marketOpen;
    const isAfterHours = currentTime >= marketClose && currentTime < 20;

    let status, message;
    let timeLeft = '';

    if (isHoliday) {
      status = 'HOLIDAY';
      message = 'Market Holiday';
    } else if (!isWeekday) {
      status = 'WEEKEND';
      message = 'Weekend Market Closure';
    } else if (isPreMarket) {
      status = 'PRE-MARKET';
      message = 'Pre-Market Session';
    } else if (isWithinHours) {
      status = 'OPEN';
      message = 'Markets Live • Active Trading';
    } else if (isAfterHours) {
      status = 'AFTER HOURS';
      message = 'After-Hours Trading';
    } else {
      status = 'CLOSED';
      message = 'Markets Closed';
    }

    // Calculate time left
    let targetHour, targetMinute, timePhrase;

    if (isWeekday && !isHoliday) {
      if (currentTime < marketOpen) {
        targetHour = Math.floor(marketOpen);
        targetMinute = (marketOpen % 1) * 60;
        timePhrase = 'until open';
      } else if (currentTime >= marketClose) {
        targetHour = Math.floor(marketOpen + 24);
        targetMinute = (marketOpen % 1) * 60;
        timePhrase = 'until open';
      } else {
        targetHour = Math.floor(marketClose);
        targetMinute = (marketClose % 1) * 60;
        timePhrase = 'until close';
      }
    } else {
      const daysUntilMonday = (8 - day) % 7 || 7;
      targetHour = Math.floor(marketOpen + (daysUntilMonday * 24));
      targetMinute = (marketOpen % 1) * 60;
      timePhrase = 'until open';
    }

    if (timePhrase) {
      const now = new Date();
      let targetDate = new Date(now);
      
      let targetHourFinal = targetHour;
      let targetMinuteFinal = targetMinute;
      
      if (targetHourFinal >= 24) {
        const daysToAdd = Math.floor(targetHourFinal / 24);
        targetDate.setDate(targetDate.getDate() + daysToAdd);
        targetHourFinal = targetHourFinal % 24;
      }
      
      targetDate.setHours(Math.floor(targetHourFinal), Math.round(targetMinuteFinal), 0, 0);
      
      const diffMs = targetDate - now;
      if (diffMs > 0) {
        const totalSeconds = Math.floor(diffMs / 1000);
        const diffHrs = Math.floor(totalSeconds / 3600);
        const diffMins = Math.floor((totalSeconds % 3600) / 60);
        const diffSecs = totalSeconds % 60;
        timeLeft = `${String(diffHrs).padStart(2, '0')}h ${String(diffMins).padStart(2, '0')}m ${String(diffSecs).padStart(2, '0')}s ${timePhrase}`;
      }
    }

    return {
      isOpen: status === 'OPEN',
      status,
      message,
      timeLeft,
      isPreMarket,
      isAfterHours,
      isWeekday,
      isHoliday
    };
  };

  useEffect(() => {
    const updateStatus = () => {
      setMarketStatus(getMarketStatus());
      setCurrentTime(new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
      }));
    };

    updateStatus();
    const interval = setInterval(updateStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  const getProgressWidth = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const currentTime = hours + minutes / 60;
    
    if (marketStatus.isOpen) {
      const progress = ((currentTime - 9.5) / (16 - 9.5)) * 100;
      return Math.min(Math.max(progress, 0), 100);
    }
    return 0;
  };

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
        
        {/* Premium Market Status Box */}
        <div className="market-status-box">
          <div className="status-glow"></div>
          <div className="status-shimmer"></div>
          <div className={`status-indicator ${marketStatus.isOpen ? 'open' : 'closed'}`}>
            <div className="status-dot-container">
              <span className={`status-dot ${marketStatus.isOpen ? 'active' : ''}`}></span>
              {marketStatus.isOpen && (
                <>
                  <span className="status-pulse"></span>
                  <span className="status-pulse-delayed"></span>
                </>
              )}
              {marketStatus.isPreMarket && <span className="status-pulse-pre"></span>}
              {marketStatus.status === 'AFTER HOURS' && <span className="status-pulse-after"></span>}
            </div>
            <div className="status-content">
              <div className="status-header">
                <span className="status-label">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <rect x="2" y="2" width="20" height="20" rx="4"/>
                    <line x1="8" y1="6" x2="8" y2="18"/>
                    <line x1="16" y1="6" x2="16" y2="18"/>
                    <line x1="6" y1="8" x2="18" y2="8"/>
                    <line x1="6" y1="12" x2="18" y2="12"/>
                    <line x1="6" y1="16" x2="18" y2="16"/>
                  </svg>
                  MARKET STATUS
                </span>
                <div className="status-badge-group">
                  <span className={`status-badge ${marketStatus.isOpen ? 'open' : marketStatus.isPreMarket ? 'pre' : marketStatus.status === 'AFTER HOURS' ? 'after' : 'closed'}`}>
                    {marketStatus.isOpen ? '● LIVE' : marketStatus.isPreMarket ? '◐ PRE' : marketStatus.status === 'AFTER HOURS' ? '◑ AH' : '○ CLOSED'}
                  </span>
                  <span className="status-timestamp">{currentTime}</span>
                </div>
              </div>
              <div className="status-message-wrapper">
                <span className="status-message">{marketStatus.message}</span>
                {marketStatus.timeLeft && (
                  <span className="status-time-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    {marketStatus.timeLeft}
                  </span>
                )}
              </div>
              <div className="status-progress">
                <div className={`status-progress-bar ${marketStatus.isOpen ? 'open' : ''}`} style={{ width: `${getProgressWidth()}%` }}></div>
              </div>
            </div>
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

export default Feed;