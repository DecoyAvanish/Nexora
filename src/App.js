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