import React, { useState } from 'react'
import logo from './logo.svg';
import './App.css';
import Header from './Header';
import Feed from './Feed';
import Stats from './Stats';
import Stocks from './Stocks';

function App() {
  // Simple routing state
  const [currentPage, setCurrentPage] = useState('portfolio');

  const renderPage = () => {
    switch(currentPage) {
      case 'stocks':
        return <Stocks />;
      case 'portfolio':
      default:
        return (
          <div className="body">
            <div className="info">
              <Feed />
              <Stats />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="App">
      <div className="header">
        <Header onNavigate={setCurrentPage} currentPage={currentPage} />
      </div>
      {renderPage()}
    </div>
  );
}

export default App;