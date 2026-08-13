import React, { useState, useEffect } from 'react';
import { auth, signOut, database, updateProfile } from './firebase';
import { doc, getDoc, updateDoc, onSnapshot } from 'firebase/firestore';
import './Account.css';

function Account({ user, onLogout }) {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!user) return;

    const userDocRef = doc(database, 'users', user.uid);
    
    const unsubscribe = onSnapshot(userDocRef, (doc) => {
      if (doc.exists()) {
        setUserData(doc.data());
        setDisplayName(doc.data().displayName || '');
      } else {
        console.log('No user data found');
      }
      setLoading(false);
    }, (error) => {
      console.error('Error fetching user data:', error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

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
        <p>Loading your account...</p>
      </div>
    );
  }

  return (
    <div className="account-container">
      <div className="account-header">
        <h1>Account Settings</h1>
        <p>Manage your Nexora account</p>
      </div>

      <div className="account-grid">
        {/* Profile Section */}
        <div className="account-card profile-card">
          <div className="profile-header">
            <div className="profile-avatar">
              {userData?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </div>
            <div className="profile-info">
              <h2>{userData?.displayName || user?.displayName || 'User'}</h2>
              <p>{user?.email}</p>
            </div>
          </div>
          
          {editMode ? (
            <form onSubmit={handleUpdateProfile} className="edit-form">
              <div className="form-group">
                <label>Display Name</label>
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
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => {
                    setEditMode(false);
                    setDisplayName(userData?.displayName || '');
                    setError('');
                    setSuccess('');
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          ) : (
            <div className="profile-actions">
              <button 
                className="btn-edit" 
                onClick={() => setEditMode(true)}
              >
                ✏️ Edit Profile
              </button>
            </div>
          )}
        </div>

        {/* Account Stats */}
        <div className="account-card stats-card">
          <h3>Account Summary</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Member Since</span>
              <span className="stat-value">
                {userData?.createdAt 
                  ? new Date(userData.createdAt).toLocaleDateString()
                  : 'N/A'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Account Status</span>
              <span className="stat-value status-active">Active ✓</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Cash Balance</span>
              <span className="stat-value">
                ${userData?.portfolio?.cash?.toFixed(2) || '10,000.00'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Holdings</span>
              <span className="stat-value">
                {userData?.portfolio?.holdings?.length || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div className="account-card security-card">
          <h3>Security</h3>
          <div className="security-item">
            <div className="security-info">
              <span className="security-label">Email</span>
              <span className="security-value">{user?.email}</span>
            </div>
            <button className="btn-secondary">Change Email</button>
          </div>
          <div className="security-item">
            <div className="security-info">
              <span className="security-label">Password</span>
              <span className="security-value">••••••••</span>
            </div>
            <button className="btn-secondary">Change Password</button>
          </div>
        </div>

        {/* Logout Section */}
        <div className="account-card logout-card">
          <button 
            className="btn-logout" 
            onClick={handleLogout}
          >
            🚪 Sign Out
          </button>
          <p className="logout-hint">
            You will be redirected to the login page
          </p>
        </div>
      </div>
    </div>
  );
}

export default Account;