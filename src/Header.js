import React from 'react';
import './Header.css';

function Header({ onNavigate, currentPage, user, onLogout }) {
  const navItems = [
    { id: 'portfolio', label: 'Portfolio' },
    { id: 'stocks', label: 'Stocks' },
    { id: 'cash', label: 'Cash' },
  ];

  const handleNavClick = (e, id) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate(id);
    }
  };

  return (
    <div className="header-wrapper">
      <div className="header-container">
        <div className="header-glass">
          <div className="header-inner">
            <div className="logo" onClick={() => onNavigate && onNavigate('portfolio')}>
              <div className="logo-icon">◆</div>
              <span>NEXORA</span>
            </div>
            
            <div className="searchbar">
              <div className="searchcontainer">
                <span className="search-icon">⌕</span>
                <input placeholder="Search assets..." type="text" />
                <span className="search-shortcut">⌘K</span>
              </div>
            </div>
            
            <div className="menu">
              {navItems.map((item) => (
                <a
                  key={item.id}
                  href="#"
                  onClick={(e) => handleNavClick(e, item.id)}
                  className={currentPage === item.id ? 'active' : ''}
                >
                  {item.label}
                </a>
              ))}
              
              {user && (
                <div className="user-profile" onClick={() => onNavigate && onNavigate('account')}>
                  <div className="user-avatar">
                    {user.displayName?.[0] || user.email?.[0] || 'U'}
                  </div>
                  <div className="user-info-text">
                    <span className="user-name">
                      {user.displayName || user.email?.split('@')[0] || 'User'}
                    </span>
                    <span className="user-email">{user.email || 'user@nexora.com'}</span>
                  </div>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Header;