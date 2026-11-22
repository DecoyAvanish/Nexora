import React, { useEffect, useRef, useState } from 'react';
import './Header.css';

function Header({ onNavigate, currentPage, user, onLogout }) {
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef(null);
  const primaryItems = [
    { id: 'portfolio', label: 'Portfolio' },
    { id: 'stocks', label: 'Stocks' },
    { id: 'research', label: 'Research' },
    { id: 'modelLab', label: 'Model Lab' },
  ];
  const secondaryItems = [
    { id: 'cash', label: 'Cash' },
    { id: 'risk', label: 'Risk Lab' },
    { id: 'decisions', label: 'Decision Lab' },
    { id: 'modelCard', label: 'Model Card' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'status', label: 'Status' },
    { id: 'demo', label: 'Demo' },
  ];
  const routeHash = (id) => ({ modelLab: 'model-lab', modelCard: 'model-card' }[id] || id);

  useEffect(() => {
    const close = (event) => {
      if (moreRef.current && !moreRef.current.contains(event.target)) setMoreOpen(false);
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, []);

  const handleNavClick = (e, id) => {
    e.preventDefault();
    setMoreOpen(false);
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
            
            <div className="menu" role="navigation" aria-label="Workspace">
              {primaryItems.map((item) => (
                <a
                  key={item.id}
                  href={`#${routeHash(item.id)}`}
                  onClick={(e) => handleNavClick(e, item.id)} aria-current={currentPage === item.id ? 'page' : undefined}
                  className={currentPage === item.id ? 'active' : ''}
                >
                  {item.label}
                </a>
              ))}

              <div className="more-menu" ref={moreRef}>
                <button
                  type="button"
                  className={`more-trigger ${secondaryItems.some(item => item.id === currentPage) ? 'active' : ''}`}
                  aria-expanded={moreOpen}
                  onClick={() => setMoreOpen(open => !open)}
                >
                  More <span aria-hidden="true">⌄</span>
                </button>
                {moreOpen && (
                  <div className="more-panel">
                    {secondaryItems.map(item => (
                      <a
                        key={item.id}
                        href={`#${routeHash(item.id)}`}
                        onClick={(event) => handleNavClick(event, item.id)} aria-current={currentPage === item.id ? 'page' : undefined}
                        className={currentPage === item.id ? 'active' : ''}
                      >
                        {item.label}
                      </a>
                    ))}
                  </div>
                )}
              </div>
              
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
