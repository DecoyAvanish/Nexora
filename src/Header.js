import React from 'react';
import Logo from './robinhood.svg';
import './Header.css';

function Header({ onNavigate, currentPage, user, onLogout }) {
  const navItems = [
    { id: 'portfolio', label: 'Portfolio' },
    { id: 'stocks', label: 'Stocks' },
    { id: 'account', label: 'Account' },
  ];

  const handleNavClick = (e, id) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate(id);
    }
  };

  return (
    <div className="wrapper">
      <div className="logo" onClick={() => onNavigate && onNavigate('portfolio')}>
        <img src={Logo} width={25} alt="Nexora" />
      </div>
      <div className="searchbar">
        <div className="searchcontainer">
          <input placeholder="Search" type="text" />
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
          <div className="user-info">
            <span className="user-avatar">
              {user.displayName?.[0] || user.email?.[0] || 'U'}
            </span>
            <span className="user-name">
              {user.displayName || user.email?.split('@')[0] || 'User'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Header;