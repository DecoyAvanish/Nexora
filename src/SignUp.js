import React, { useState } from 'react';
import { 
  auth, 
  createUserWithEmailAndPassword, 
  updateProfile, 
  database 
} from './firebase';
import { doc, setDoc } from 'firebase/firestore';
import './Auth.css';

function SignUp({ onSignUp, onSwitchToLogin }) {
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      await updateProfile(user, { displayName });

      await setDoc(doc(database, 'users', user.uid), {
        uid: user.uid,
        email: user.email,
        displayName: displayName,
        createdAt: new Date().toISOString(),
        portfolio: {
          cash: 10000,
          holdings: []
        },
        watchlist: [],
        settings: {
          theme: 'dark',
          notifications: true
        }
      });

      onSignUp();
    } catch (err) {
      console.error('Sign up error:', err);
      switch (err.code) {
        case 'auth/email-already-in-use':
          setError('This email is already registered.');
          break;
        case 'auth/invalid-email':
          setError('Invalid email address.');
          break;
        case 'auth/weak-password':
          setError('Password is too weak. Please use a stronger password.');
          break;
        default:
          setError('Failed to create account. Please try again.');
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
              <span className="icon">🚀</span>
            </div>
          </div>
          <h1>Forge Your Legacy</h1>
          <p className="subtitle">Join the <span>Nexora</span> Revolution</p>
        </div>
        
        <form onSubmit={handleSignUp} className="form">
          <div className="group">
            <label>Full Name</label>
            <div className="wrapper">
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your Identity"
                required
              />
              <span className="icon">◈</span>
            </div>
          </div>
          
          <div className="group">
            <label>Email Address</label>
            <div className="wrapper">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@empire.com"
                required
              />
              <span className="icon">⌘</span>
            </div>
          </div>
          
          <div className="group">
            <label>Secret Key</label>
            <div className="wrapper">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create your code"
                required
              />
              <span className="icon">⚡</span>
            </div>
            <small className="hint">Minimum 6 characters • Must be unbreakable</small>
          </div>
          
          <div className="group">
            <label>Confirm Secret Key</label>
            <div className="wrapper">
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Verify your code"
                required
              />
              <span className="icon">✓</span>
            </div>
          </div>
          
          {error && <div className="error">{error}</div>}
          
          <button type="submit" className="btn" disabled={loading}>
            <span className="content">
              {loading ? 'Forging Account...' : 'Start Your Empire'}
              <span className="arrow">→</span>
            </span>
          </button>
        </form>
        
        <div className="divider">
          <span>or</span>
        </div>
        
        <div className="footer">
          <p>
            Already have an account?{' '}
            <button 
              className="switchbtn" 
              onClick={onSwitchToLogin}
            >
              Enter the Terminal
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

export default SignUp;