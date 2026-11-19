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
import DecisionLab from './DecisionLab';
import PublicShowcase from './PublicShowcase';
import AppErrorBoundary from './AppErrorBoundary';
import { auth, onAuthStateChanged } from './firebase';

const ROUTE_HASHES = {'#portfolio':'portfolio','#stocks':'stocks','#cash':'cash','#risk':'risk','#research':'research','#decisions':'decisions','#model-lab':'modelLab','#model-card':'modelCard','#architecture':'architecture','#status':'status','#demo':'demo'};
const HASHES_BY_ROUTE = Object.fromEntries(Object.entries(ROUTE_HASHES).map(([hash, route]) => [route, hash.slice(1)]));
const GUEST_TEST_ROUTES = new Set(['stocks', 'cash', 'risk', 'research', 'decisions', 'modelLab', 'modelCard', 'architecture', 'status', 'demo']);

function App() {
  const [user, setUser] = useState(null);
  const initialRoute = ROUTE_HASHES[window.location.hash] || 'portfolio';
  const [loading, setLoading] = useState(!GUEST_TEST_ROUTES.has(initialRoute));
  const [currentPage, setCurrentPage] = useState(initialRoute);
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
    const timeout = window.setTimeout(() => setLoading(false), 2500);
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      window.clearTimeout(timeout);
      setUser(user);
      setLoading(false);
      if (user) {
        setShowAuth('login');
      }
    });

    return () => {
      window.clearTimeout(timeout);
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    const handleHashChange = () => setCurrentPage(ROUTE_HASHES[window.location.hash] || 'portfolio');
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleNavigate = (page) => {
    setCurrentPage(page);
    if (HASHES_BY_ROUTE[page]) window.location.hash = HASHES_BY_ROUTE[page];
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
    if (['modelCard','architecture','status','demo'].includes(currentPage)) return <PublicShowcase key={currentPage} page={currentPage} onNavigate={handleNavigate} />;
    if (!user && !GUEST_TEST_ROUTES.has(currentPage)) {
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
      case 'decisions':
        return <DecisionLab />;
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
  const showHeader = GUEST_TEST_ROUTES.has(currentPage) || (user && ['portfolio', 'account'].includes(currentPage));

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
      <AppErrorBoundary resetKey={currentPage}>{renderContent()}</AppErrorBoundary>
    </div>
  );
}

export default App;
