import React, { useState, useEffect, useRef } from 'react';
import { auth, signOut, database, updateProfile } from './firebase';
import { doc, getDoc, updateDoc, onSnapshot } from 'firebase/firestore';
import './Account.css';

function useCountUp(target, duration = 700) {
  const [value, setValue] = useState(target || 0);
  const fromRef = useRef(target || 0);

  useEffect(() => {
    const from = fromRef.current;
    const to = target || 0;
    if (from === to) return;

    let start;
    let raf;
    const step = (ts) => {
      if (start === undefined) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(from + (to - from) * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
      else fromRef.current = to;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);

  return value;
}

function Account({ user, onLogout }) {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const cash = useCountUp(userData?.portfolio?.cash ?? 10000);

  useEffect(() => {
    if (!user) return;

    const userDocRef = doc(database, 'users', user.uid);
    const unsubscribe = onSnapshot(userDocRef, (doc) => {
      if (doc.exists()) {
        setUserData(doc.data());
        setDisplayName(doc.data().displayName || '');
      }
      setLoading(false);
    }, (error) => {
      console.error('Error fetching user data:', error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleIdentityMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mx = ((e.clientX - rect.left) / rect.width) * 100;
    const my = ((e.clientY - rect.top) / rect.height) * 100;
    e.currentTarget.style.setProperty('--mx', `${mx}%`);
    e.currentTarget.style.setProperty('--my', `${my}%`);
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      onLogout();
    } catch (err) {
      console.error('Logout error:', err);
      setError('Failed to logout. Please try again.');
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await updateProfile(auth.currentUser, { displayName });
      const userDocRef = doc(database, 'users', user.uid);
      await updateDoc(userDocRef, {
        displayName: displayName,
        updatedAt: new Date().toISOString()
      });

      setSuccess('Profile updated successfully!');
      setEditMode(false);
    } catch (err) {
      console.error('Update error:', err);
      setError('Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !userData) {
    return (
      <div className="account-loading">
        <div className="loading-spinner"></div>
        <p>INITIALIZING SYSTEM</p>
      </div>
    );
  }

  return (
    <div className="account-container">
      {/* Layered ambient background — grid, faint chart geometry,
          drifting data points, and a slow vertical scan sweep */}
      <div className="bg-grid"></div>
      <div className="bg-chartlines">
        <svg viewBox="0 0 1000 700" preserveAspectRatio="none">
          <polyline
            points="0,520 120,500 220,460 300,480 420,380 540,410 640,300 760,330 860,220 1000,250"
            fill="none"
            stroke="rgba(61,240,224,0.5)"
            strokeWidth="1"
          />
          <polyline
            points="0,180 140,210 260,160 380,190 500,120 620,150 740,90 860,110 1000,60"
            fill="none"
            stroke="rgba(124,140,255,0.35)"
            strokeWidth="1"
          />
          <line x1="0" y1="640" x2="1000" y2="560" stroke="rgba(61,240,224,0.2)" strokeWidth="1" />
        </svg>
      </div>
      <div className="bg-particles">
        {[...Array(14)].map((_, i) => (
          <div key={i} className="bg-particle" style={{
            '--delay': `${i * 1.4}s`,
            '--duration': `${18 + Math.random() * 12}s`,
            '--x': `${Math.random() * 100}%`,
            '--size': `${1 + Math.random() * 1.5}px`,
          }}></div>
        ))}
      </div>
      <div className="bg-scanline"></div>

      {/* Mouse follower glow */}
      <div className="cursor-glow" style={{
        left: mousePosition.x,
        top: mousePosition.y
      }}></div>

      {/* Header */}
      <div className="account-header">
        <div className="header-main">
          <div className="header-label">
            <span>NEXORA // OS</span>
            <span>ACCOUNT NODE // 07</span>
            <span className="status-dot"></span>
            <span>ONLINE</span>
          </div>
          <h1>
            <span className="title-account">ACCOUNT</span>{' '}
            <span className="title-settings">SETTINGS</span>
          </h1>
          <div className="header-status">
            <span className="status-time">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
        <div className="header-meta">
          <span>NXR // 001</span>
          <span>SECURE NODE</span>
          <span>USER SYSTEM</span>
        </div>
      </div>

      {/* Profile identity module */}
      <div className="identity-module" onMouseMove={handleIdentityMove}>
        <div className="identity-ring">
          <div className="identity-avatar">
            <span>{userData?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}</span>
            <div className="identity-ring-orbital"></div>
            <div className="identity-ring-orbital-2"></div>
            <div className="identity-status-indicator"></div>
          </div>
        </div>
        <div className="identity-info">
          <h2>{userData?.displayName || user?.displayName || 'User'}</h2>
          <p>{user?.email}</p>
          <div className="identity-badge">
            <span>VERIFIED</span>
            <span className="badge-prime">PRIME</span>
          </div>
        </div>
        <button
          className="identity-control"
          onClick={() => setEditMode(!editMode)}
        >
          <span>◈</span>
          {editMode ? 'CLOSE' : 'EDIT PROFILE'}
        </button>
      </div>

      {/* Edit form */}
      {editMode && (
        <div className="edit-module">
          <form onSubmit={handleUpdateProfile} className="edit-form">
            <div className="edit-group">
              <label>IDENTITY</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                required
              />
            </div>
            {error && <div className="form-error">{error}</div>}
            {success && <div className="form-success">{success}</div>}
            <div className="edit-actions">
              <button type="button" className="btn-secondary" onClick={() => {
                setEditMode(false);
                setDisplayName(userData?.displayName || '');
                setError('');
                setSuccess('');
              }}>
                CANCEL
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'UPDATING...' : 'UPDATE IDENTITY'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Financial telemetry — one connected system, not four loose cards */}
      <div className="telemetry-system">
        <div className="telemetry-rail">TELEMETRY // LIVE</div>
        <div className="telemetry-grid">
          <div className="telemetry-card telemetry-dominant">
            <span className="telemetry-coord">N.01</span>
            <div className="telemetry-label">
              <span>LIQUID CAPITAL</span>
              <span className="telemetry-ticker">● LIVE</span>
            </div>
            <div className="telemetry-value">
              ${cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="telemetry-waveform">
              {[...Array(12)].map((_, i) => <div key={i} className="waveform-line"></div>)}
            </div>
          </div>

          <div className="telemetry-card">
            <span className="telemetry-coord">N.02</span>
            <div className="telemetry-label">MEMBER SINCE</div>
            <div className="telemetry-value small">
              {userData?.createdAt
                ? new Date(userData.createdAt).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                  }).replace(/\//g, '.')
                : 'N/A'}
            </div>
            <div className="telemetry-meta">REGISTERED</div>
          </div>

          <div className="telemetry-card">
            <span className="telemetry-coord">N.03</span>
            <div className="telemetry-label">ACCOUNT STATUS</div>
            <div className="telemetry-value small">
              <span className="status-active">
                <span className="status-ping"></span>
                ACTIVE
              </span>
            </div>
            <div className="telemetry-meta">SECURE</div>
          </div>

          <div className="telemetry-card">
            <span className="telemetry-coord">N.04</span>
            <div className="telemetry-label">HOLDINGS</div>
            <div className="telemetry-value small">
              {userData?.portfolio?.holdings?.length || 0}
            </div>
            <div className="holdings-spark">
              {[...Array(6)].map((_, i) => <div key={i} className="waveform-line"></div>)}
            </div>
          </div>
        </div>
      </div>

      {/* Security command center */}
      <div className="security-module">
        <div className="security-header">
          <div className="security-title">
            <span className="security-icon">◈</span>
            <h3>SECURITY PROTOCOL</h3>
            <span className="security-badge">● ENCRYPTED</span>
          </div>
          <div className="security-meta">
            <span>PROTECTION LEVEL: HIGH</span>
          </div>
        </div>

        <div className="security-grid">
          <div className="security-item">
            <div className="security-info">
              <span className="security-label">IDENTITY</span>
              <span className="security-value">{user?.email}</span>
            </div>
            <button className="security-control">VERIFY</button>
          </div>

          <div className="security-item">
            <div className="security-info">
              <span className="security-label">SESSION</span>
              <span className="security-value">SECURE</span>
            </div>
            <button className="security-control">REFRESH</button>
          </div>

          <div className="security-item">
            <div className="security-info">
              <span className="security-label">PASSWORD</span>
              <span className="security-value masked">••••••••</span>
            </div>
            <button className="security-control">ROTATE</button>
          </div>
        </div>

        <div className="security-footer">
          <span>LAST SECURITY CHECK: {new Date().toLocaleString()}</span>
          <span>NEXORA // SECURE PROTOCOL v3.2.1</span>
        </div>
      </div>

      {/* Terminate session */}
      <div className="terminate-module">
        <button className="terminate-btn" onClick={handleLogout}>
          <span className="terminate-icon">⏻</span>
          <span className="terminate-text">TERMINATE SESSION</span>
          <span className="terminate-warning">●</span>
        </button>
        <p className="terminate-hint">SYSTEM LOCK // SECURE EXIT</p>
      </div>
    </div>
  );
}

export default Account;