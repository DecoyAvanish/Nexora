// Header.js - Updated with navigation
import React from 'react';
import Logo from './robinhood.svg';
import './Header.css';

function Header({ onNavigate, currentPage }) {
  const navItems = [
    { id: 'stocks', label: 'Stocks' },
    { id: 'portfolio', label: 'Portfolio' },
    { id: 'cash', label: 'Cash' },
    { id: 'messages', label: 'Messages' },
    { id: 'account', label: 'Account' },
  ];

  return (
    <div className="wrapper">
      <div className="logo">
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
            onClick={(e) => {
              e.preventDefault();
              onNavigate(item.id);
            }}
            className={currentPage === item.id ? 'active' : ''}
          >
            {item.label}
          </a>
        ))}
      </div>
    </div>
  );
}

export default Header;