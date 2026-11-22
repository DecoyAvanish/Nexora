import React, { useState } from 'react';
import { signInWithEmailAndPassword, auth } from './firebase';
import './Auth.css';

function Login({ onLogin, onSwitchToSignUp }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signInWithEmailAndPassword(auth, email, password);
      onLogin();
    } catch (err) {
      console.error('Login error:', err);
      switch (err.code) {
        case 'auth/user-not-found':
          setError('No account found with this email.');
          break;
        case 'auth/wrong-password':
          setError('Incorrect password. Please try again.');
          break;
        case 'auth/invalid-email':
          setError('Invalid email address.');
          break;
        case 'auth/too-many-requests':
          setError('Too many failed attempts. Please try again later.');
          break;
        default:
          setError('Failed to login. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="authcontainer">
      <div className="field">
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
      </div>
      
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      
      <div className="overlay"></div>
      
      <div className="card">
        <div className="header">
          <div className="logo">
            <div className="ring">
              <span className="icon">📈</span>
            </div>
          </div>
          <h1>Sign in to Nexora</h1>
          <p className="subtitle">Open your portfolio and research workspace.</p>
        </div>
        
        <form onSubmit={handleLogin} className="form">
          <div className="group">
            <label>Username / Email</label>
            <div className="wrapper">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@edge.com"
                required
              />
              <span className="icon">⌘</span>
            </div>
          </div>
          
          <div className="group">
            <label>Access Key</label>
            <div className="wrapper">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <span className="icon">⚡</span>
            </div>
          </div>
          
          {error && <div className="error">{error}</div>}
          
          <button type="submit" className="btn" disabled={loading}>
            <span className="content">
              {loading ? 'Signing in…' : 'Sign in'}
              <span className="arrow">→</span>
            </span>
          </button>
        </form>
        
        <div className="divider">
          <span>or</span>
        </div>
        
        <div className="footer">
          <p>
            New to Nexora?{' '}
            <button 
              className="switchbtn" 
              onClick={onSwitchToSignUp}
            >
              Create an account
            </button>
          </p>
        </div>
        
        <div className="status">
          <span className="dot"></span>
          System Online • v3.2.1
        </div>
      </div>
    </div>
  );
}

export default Login;
