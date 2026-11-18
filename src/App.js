// App.js (updated)
import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './Header';
import Feed from './Feed';
import Stats from './Stats';
import Stocks from './Stocks';
import Cash from './Cash';
import Login from './Login';
import SignUp from './SignUp';
import Account from './Account';
import ModelLab from './ModelLab';
import RiskLab from './RiskLab';
import ResearchLab from './ResearchLab';
import { auth, onAuthStateChanged } from './firebase';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(
    window.location.hash === '#model-lab' ? 'modelLab' : 'portfolio'
  );
  const [showAuth, setShowAuth] = useState('login');

  const orbs = Array.from({ length: 4 }, (_, i) => {
    const size = 250 + Math.random() * 350;
    const x = 10 + Math.random() * 80;
    const duration = 35 + Math.random() * 30;
    const delay = Math.random() * 30;
    const type = ['orb-purple', 'orb-pink', 'orb-blue'][Math.floor(Math.random() * 3)];
    return { id: i, size, x, duration, delay, type };
  });

  const particles = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    size: 1.5 + Math.random() * 2.5,
    x: 5 + Math.random() * 90,
    duration: 25 + Math.random() * 25,
    delay: Math.random() * 25,
  }));

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
      if (user) {
        setShowAuth('login');
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const handleHashChange = () => {
      if (window.location.hash === '#model-lab') setCurrentPage('modelLab');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleNavigate = (page) => {
    setCurrentPage(page);
    if (page === 'modelLab') window.location.hash = 'model-lab';
    else if (window.location.hash === '#model-lab') window.history.replaceState(null, '', window.location.pathname);
  };

  const handleLogin = () => {
    setUser(auth.currentUser);
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentPage('portfolio');
  };

  const handleSwitchToSignUp = () => {
    setShowAuth('signup');
  };

  const handleSwitchToLogin = () => {
    setShowAuth('login');
  };

  const renderSpaceBackground = () => (
    <div className="bg-space">
      <div className="bg-stars"></div>
      <div className="bg-grid-overlay"></div>
      {orbs.map((orb) => (
        <div 
          key={orb.id}
          className={`space-orb ${orb.type}`}
          style={{
            width: orb.size + 'px',
            height: orb.size + 'px',
            left: orb.x + '%',
            '--duration': orb.duration + 's',
            '--delay': orb.delay + 's'
          }}
        />
      ))}
      {particles.map((particle) => (
        <div 
          key={particle.id}
          className="space-particle"
          style={{
            '--size': particle.size + 'px',
            left: particle.x + '%',
            '--duration': particle.duration + 's',
            '--delay': particle.delay + 's'
          }}
        />
      ))}
    </div>
  );

  const renderContent = () => {
    if (currentPage === 'modelLab') return <ModelLab />;
    if (!user) {
      if (showAuth === 'signup') {
        return (
          <SignUp 
            onSignUp={handleLogin} 
            onSwitchToLogin={handleSwitchToLogin} 
          />
        );
      }
      return (
        <Login 
          onLogin={handleLogin} 
          onSwitchToSignUp={handleSwitchToSignUp} 
        />
      );
    }

    switch(currentPage) {
      case 'stocks':
        return <Stocks />;
      case 'cash':
        return <Cash />;
      case 'risk':
        return <RiskLab />;
      case 'research':
        return <ResearchLab />;
      case 'account':
        return <Account user={user} onLogout={handleLogout} />;
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

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading Nexora...</p>
      </div>
    );
  }

  // Check if user is authenticated and on a page that should show the header
  const showHeader = currentPage === 'modelLab' || (user && ['portfolio', 'stocks', 'cash', 'risk', 'research', 'account'].includes(currentPage));

  return (
    <div className="App">
      {user && currentPage === 'portfolio' && renderSpaceBackground()}

      {showHeader && (
        <div className="header">
          <Header
            onNavigate={handleNavigate}
            currentPage={currentPage}
            user={user}
            onLogout={handleLogout}
          />
        </div>
      )}
      {renderContent()}
    </div>
  );
}

export default App;
