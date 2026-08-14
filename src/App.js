import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './Header';
import Feed from './Feed';
import Stats from './Stats';
import Stocks from './Stocks';
import Login from './Login';
import SignUp from './SignUp';
import Account from './Account';
import { auth, onAuthStateChanged } from './firebase';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState('portfolio');
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

    if (currentPage === 'stocks') {
      return <Stocks />;
    }
    
    if (currentPage === 'account') {
      return <Account user={user} onLogout={handleLogout} />;
    }

    return (
      <div className="body">
        <div className="info">
          <Feed />
          <Stats />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading Nexora...</p>
      </div>
    );
  }

  return (
    <div className="App">
      {user && currentPage === 'portfolio' && renderSpaceBackground()}

      <div className="header">
        <Header 
          onNavigate={setCurrentPage} 
          currentPage={currentPage}
          user={user}
          onLogout={handleLogout}
        />
      </div>
      {renderContent()}
    </div>
  );
}

export default App;